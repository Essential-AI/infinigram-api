import logging
from hashlib import sha256
from typing import Dict, List
from uuid import uuid4

from opentelemetry import trace
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import SpanKind, Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from pydantic import ValidationError
from redis.asyncio import Redis
from saq import Queue

from src.attribution.attribution_queue_service import AttributionQueueDependency
from src.attribution.attribution_request import AttributionRequest
from src.attribution.attribution_service import AttributionService, AttributionTimeoutError
from src.attribution.attribution_models_v2 import (
    V2AttributionResponse, 
    V2Document, 
    V2Snippet, 
    V2Span,
    V2NestedSpan
)
from src.cache import CacheDependency
from src.config import get_config
from src.documents.documents_router import DocumentsServiceDependency
from src.documents.documents_service import DocumentsService
from src.infinigram.infini_gram_dependency import InfiniGramProcessorDependency

tracer = trace.get_tracer(get_config().application_name)
logger = logging.getLogger("uvicorn.error")


class AttributionServiceV2:
    """Service for handling v2 attribution requests with new response format"""
    
    def __init__(
        self,
        infini_gram_processor: InfiniGramProcessorDependency,
        documents_service: DocumentsServiceDependency,
        attribution_queue: AttributionQueueDependency,
        cache: CacheDependency,
    ):
        # Reuse the existing attribution service for the underlying work
        self.attribution_service = AttributionService(
            infini_gram_processor, documents_service, attribution_queue, cache
        )
        self.cache = cache

    def _get_cache_key_v2(self, index: str, request: AttributionRequest) -> bytes:
        """Generate cache key for v2 responses"""
        combined_index_and_request = (
            f"v2::{request.__class__.__qualname__}::{index}{request.model_dump_json()}"
        )
        key = sha256(
            combined_index_and_request.encode("utf-8", errors="ignore")
        ).digest()
        return key

    @tracer.start_as_current_span("attribution_service_v2/_get_cached_response")
    async def _get_cached_response_v2(
        self, index: str, request: AttributionRequest
    ) -> V2AttributionResponse | None:
        """Get cached v2 response"""
        key = self._get_cache_key_v2(index, request)

        try:
            cached_json = await self.cache.getex(key, ex=43_200)
            if cached_json is None:
                return None

            cached_response = V2AttributionResponse.model_validate_json(cached_json)
            current_span = trace.get_current_span()
            current_span.add_event("retrieved-cached-attribution-response-v2")
            logger.debug("Retrieved cached v2 attribution response")
            return cached_response

        except ValidationError:
            logger.error("Failed to parse cached v2 response", exc_info=True)
        except Exception:
            logger.error("Failed to retrieve cached v2 response", exc_info=True)

        return None

    @tracer.start_as_current_span("attribution_service_v2/_cache_response")
    async def _cache_response_v2(
        self, index: str, request: AttributionRequest, json_response: str
    ) -> None:
        """Cache v2 response"""
        key = self._get_cache_key_v2(index, request)

        try:
            await self.cache.set(key, json_response, ex=3_600)
            current_span = trace.get_current_span()
            current_span.add_event("cached-attribution-response-v2")
            logger.debug("Saved v2 attribution response to cache")
        except Exception:
            logger.warning("Failed to cache v2 attribution response", exc_info=True)

    def _transform_to_v2_format(self, index: str, original_response) -> V2AttributionResponse:
        """Transform the original attribution response to v2 format"""
        
        # Create document lookup for deduplication
        documents_dict: Dict[str, V2Document] = {}
        v2_spans: List[V2Span] = []
        
        # Process each span from the original response
        for span in original_response.spans:
            # Create document references for this span
            span_doc_ids = []
            
            for doc in span.documents:
                doc_id = str(doc.index)
                span_doc_ids.append(doc_id)
                
                # Only add document if not already processed
                if doc_id not in documents_dict:
                    # Create snippet from the document's text_snippet
                    snippets = [V2Snippet(text=doc.text_snippet)] if hasattr(doc, 'text_snippet') and doc.text_snippet else []
                    
                    # Transform the document to v2 format
                    v2_doc = V2Document(
                        index=doc_id,
                        display_name=getattr(doc, 'display_name', 'Unknown Dataset'),
                        relevance_score=getattr(doc, 'relevance_score', 0.0),
                        secondary_name=getattr(doc, 'secondary_name', 'web corpus'),
                        corresponding_span_texts=[span.text],  # Text from this span
                        corresponding_spans=[len(v2_spans)],  # Index of current span
                        snippets=snippets,
                        text_long=getattr(doc, 'text_long', doc.text if hasattr(doc, 'text') else ''),
                        title=getattr(doc, 'title', None),
                        source=getattr(doc, 'source', 'unknown'),
                        source_url=getattr(doc, 'source_url', ''),
                        usage=getattr(doc, 'usage', 'Pre-training')
                    )
                    documents_dict[doc_id] = v2_doc
                else:
                    # Update existing document with this span's information
                    existing_doc = documents_dict[doc_id]
                    if span.text not in existing_doc.corresponding_span_texts:
                        existing_doc.corresponding_span_texts.append(span.text)
                        existing_doc.corresponding_spans.append(len(v2_spans))
            
            # Create the v2 span
            v2_span = V2Span(
                start_index=span.left,
                text=span.text,
                nested_spans=[],  # For now, no nested spans - could be enhanced later
                documents=span_doc_ids
            )
            v2_spans.append(v2_span)
        
        # Convert documents dict to list
        documents_list = list(documents_dict.values())
        
        return V2AttributionResponse(
            index=index,
            spans=v2_spans,
            documents=documents_list
        )

    @tracer.start_as_current_span("attribution_service_v2/get_attribution_for_response")
    async def get_attribution_for_response_v2(
        self, index: str, request: AttributionRequest
    ) -> V2AttributionResponse:
        """Get attribution response in v2 format"""
        
        # Check cache first
        cached_response = await self._get_cached_response_v2(index, request)
        if cached_response is not None:
            return cached_response

        # Get response from original attribution service
        original_response = await self.attribution_service.get_attribution_for_response(index, request)
        
        # Transform to v2 format
        v2_response = self._transform_to_v2_format(index, original_response)
        
        # Cache the v2 response
        v2_json = v2_response.model_dump_json()
        await self._cache_response_v2(index, request, v2_json)
        
        return v2_response
