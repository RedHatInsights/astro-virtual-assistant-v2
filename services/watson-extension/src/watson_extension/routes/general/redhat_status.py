import injector
from pydantic import BaseModel
from typing import List

from quart import Blueprint
from quart_schema import validate_response, document_headers

from watson_extension.core.general.redhat_status import (
    IncidentType,
    RedhatStatusCore,
)
from watson_extension.routes import RHSessionIdHeader

blueprint = Blueprint("redhat_status", __name__, url_prefix="/redhat_status")


class ServicesOfflineResponse(BaseModel):
    response_type: str
    incidents: List[IncidentType]
    count: str


@blueprint.get("/check_services_offline")
@validate_response(ServicesOfflineResponse)
@document_headers(RHSessionIdHeader)
async def check_services_offline(
    redhat_status_service: injector.Inject[RedhatStatusCore],
) -> ServicesOfflineResponse:
    (
        response_type,
        incidents,
        count,
    ) = await redhat_status_service.check_services_offline()

    return ServicesOfflineResponse(
        response_type=response_type.value, incidents=incidents, count=count
    )
