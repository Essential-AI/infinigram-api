from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_problem.handler import generate_swagger_response

from src.attribution.attribution_request import AttributionRequest
from src.attribution.attribution_service import (
    AttributionResponse,
    AttributionService,
    AttributionTimeoutError,
)
from src.attribution.attribution_service_v2 import AttributionServiceV2
from src.attribution.attribution_models_v2 import V2AttributionResponse

attribution_router = APIRouter()


@attribution_router.post(
    path="/{index}/attribution",
    responses={
        AttributionTimeoutError.status: generate_swagger_response(
            AttributionTimeoutError  # type: ignore
        )
    },
)
async def get_document_attributions(
    index: str,
    body: AttributionRequest,
    attribution_service: Annotated[AttributionService, Depends()],
) -> AttributionResponse:
    result = await attribution_service.get_attribution_for_response(index, body)

    return result


@attribution_router.post(
    path="/{index}/attribution/v2",
    responses={
        AttributionTimeoutError.status: generate_swagger_response(
            AttributionTimeoutError  # type: ignore
        )
    },
)
async def get_document_attributions_v2(
    index: str,
    body: AttributionRequest,
    attribution_service_v2: Annotated[AttributionServiceV2, Depends()],
) -> V2AttributionResponse:
    result = await attribution_service_v2.get_attribution_for_response_v2(index, body)

    return result
