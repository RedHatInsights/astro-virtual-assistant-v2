import injector
from pydantic import BaseModel

from quart import Blueprint, render_template
from quart_schema import validate_response, validate_querystring, document_headers

from watson_extension.core.insights.image_builder import (
    ImageBuilderCore,
)
from watson_extension.routes import RHSessionIdHeader

blueprint = Blueprint("image_builder", __name__, url_prefix="/image_builder")


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
    image_builder_service: injector.Inject[ImageBuilderCore],
) -> EnableCustomRepositoriesResponse:
    version = query_args.version
    custom_repositories_response = (
        await image_builder_service.enable_custom_repositories(version)
    )

    return EnableCustomRepositoriesResponse(
        response=await render_template(
            "insights/image_builder/custom_repositories.txt.jinja",
            version=version,
            response_type=custom_repositories_response.response,
            dashboard_link="/insights/content",
        )
    )
