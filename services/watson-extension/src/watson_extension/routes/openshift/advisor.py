import injector
from pydantic import BaseModel

from quart import Blueprint, render_template
from quart_schema import validate_response, validate_querystring, document_headers

from watson_extension.core.openshift.advisor import (
    RecommendationCategory,
    AdvisorCore,
)
from watson_extension.routes import RHSessionIdHeader

blueprint = Blueprint("advisor", __name__, url_prefix="/advisor")


class RecommendationsRequestQuery(BaseModel):
    category: RecommendationCategory


class RecommendationsResponse(BaseModel):
    response: str


@blueprint.get("/recommendations")
@validate_querystring(RecommendationsRequestQuery)
@validate_response(RecommendationsResponse)
@document_headers(RHSessionIdHeader)
async def recommendations(
    query_args: RecommendationsRequestQuery,
    advisor_service: injector.Inject[AdvisorCore],
) -> RecommendationsResponse:
    recommendation_response = await advisor_service.get_recommendations(
        query_args.category
    )

    if recommendation_response.category == RecommendationCategory.RECOMMENDATION:
        category_name = "recommendations"
    elif recommendation_response.category == RecommendationCategory.WORKLOAD:
        category_name = "workloads"
    elif recommendation_response.category == RecommendationCategory.CLUSTER:
        category_name = "clusters"
    else:
        raise ValueError(f"Invalid category: {recommendation_response.category}")

    return RecommendationsResponse(
        response=await render_template(
            "openshift/advisor/recommendations.txt.jinja",
            recommendations=recommendation_response.recommendations,
            dashboard_link=recommendation_response.dashboard_link,
            category=category_name,
        )
    )
