from typing import List, Optional
from pydantic import Field

from src.camel_case_model import CamelCaseModel


class V2Document(CamelCaseModel):
    """Document model for v2 attribution response"""
    index: str = Field(description="Document index ID")
    display_name: str = Field(description="Display name of the dataset/corpus")
    relevance_score: float = Field(description="Relevance score for this document")
    secondary_name: str = Field(description="Secondary name/description of the corpus")
    corresponding_span_texts: List[str] = Field(description="Texts from corresponding spans")
    corresponding_spans: List[int] = Field(description="Indices of corresponding spans")
    snippets: List["V2Snippet"] = Field(description="Snippets from the document")
    text_long: str = Field(description="Full document text")
    title: Optional[str] = Field(default=None, description="Document title")
    source: str = Field(description="Source identifier")
    source_url: str = Field(description="Source URL")
    usage: str = Field(description="Usage description (e.g., 'Pre-training')")


class V2Snippet(CamelCaseModel):
    """Snippet model for v2 attribution response"""
    text: str = Field(description="Snippet text")


class V2NestedSpan(CamelCaseModel):
    """Nested span model for v2 attribution response"""
    start_index: int = Field(description="Start index of the nested span")
    text: str = Field(description="Text of the nested span")
    documents: List[str] = Field(description="List of document IDs for this nested span")


class V2Span(CamelCaseModel):
    """Span model for v2 attribution response"""
    start_index: int = Field(description="Start index of the span in the input text")
    text: str = Field(description="Text content of the span")
    nested_spans: List[V2NestedSpan] = Field(default=[], description="Nested spans within this span")
    documents: List[str] = Field(description="List of document IDs that contain this span")


class V2AttributionResponse(CamelCaseModel):
    """V2 Attribution response model"""
    index: str = Field(description="Index name used for attribution")
    spans: List[V2Span] = Field(description="List of attributed spans")
    documents: List[V2Document] = Field(description="List of documents referenced by spans")
