import injector
from typing import Optional
from pydantic import BaseModel

from quart import Blueprint, render_template
from quart_schema import validate_response, validate_querystring, document_headers

from watson_extension.core.insights.rhsm import (
    SubscriptionsCategory,
    RhsmCore,
)
from watson_extension.routes import RHSessionIdHeader

blueprint = Blueprint("rhsm", __name__, url_prefix="/rhsm")


class SubscriptionsCategoryQuery(BaseModel):
    category: Optional[SubscriptionsCategory] = None


class CheckSubscriptionsResponse(BaseModel):
    response: str


@blueprint.get("/check_subscriptions")
@validate_querystring(SubscriptionsCategoryQuery)
@validate_response(CheckSubscriptionsResponse)
@document_headers(RHSessionIdHeader)
async def check_subscriptions(
    query_args: SubscriptionsCategoryQuery,
    rhsm_service: injector.Inject[RhsmCore],
) -> CheckSubscriptionsResponse:
    subscriptions_info = await rhsm_service.check_subscriptions(query_args.category)
    return CheckSubscriptionsResponse(
        response=await render_template(
            "insights/rhsm/check_subscriptions.txt.jinja",
            subs_info=subscriptions_info,
        )
    )
