import injector
from pydantic import BaseModel

from quart import Blueprint, render_template
from quart_schema import validate_response, validate_querystring, document_headers

from watson_extension.core.insights.content_sources import (
    ContentSourcesCore,
)
from watson_extension.routes import RHSessionIdHeader

blueprint = Blueprint("content_sources", __name__, url_prefix="/content_sources")


class CustomRepositoriesRequestQuery(BaseModel):
    version: str


class EnableCustomRepositoriesResponse(BaseModel):
    response: str


@blueprint.get("/enable_custom_repositories")
@validate_querystring(CustomRepositoriesRequestQuery)
@validate_response(EnableCustomRepositoriesResponse)
@document_headers(RHSessionIdHeader)
async def enable_custom_repositories(
    query_args: CustomRepositoriesRequestQuery,
    content_sources_service: injector.Inject[ContentSourcesCore],
) -> EnableCustomRepositoriesResponse:
    version = query_args.version
    custom_repositories_response = (
        await content_sources_service.enable_custom_repositories(version)
    )

    return EnableCustomRepositoriesResponse(
        response=await render_template(
            "insights/content_sources/custom_repositories.txt.jinja",
            version=version,
            response_type=custom_repositories_response.response,
            dashboard_link="/insights/content",
        )
    )
