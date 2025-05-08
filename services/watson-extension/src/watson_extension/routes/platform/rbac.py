import injector
from pydantic import BaseModel

from quart import Blueprint, render_template
from quart_schema import validate_response, validate_querystring, document_headers

from watson_extension.core.platform.rbac import (
    RBACCore,
)
from watson_extension.routes import RHSessionIdHeader
from watson_extension.clients.identity import AbstractUserIdentityProvider
from common.auth import decoded_identity_header

blueprint = Blueprint("rbac", __name__, url_prefix="/rbac")


class TamAccessRequestQuery(BaseModel):
    account_id: str
    org_id: str
    duration: str


class TamAccessRequestResponse(BaseModel):
    response: str


class OrgIdResponse(BaseModel):
    response: str


@blueprint.post("/tam-access")
@validate_querystring(TamAccessRequestQuery)
@validate_response(TamAccessRequestResponse)
@document_headers(RHSessionIdHeader)
async def send_tam_access(
    query_args: TamAccessRequestQuery,
    user_identity_provider: injector.Inject[AbstractUserIdentityProvider],
    rbac_core: injector.Inject[RBACCore],
) -> TamAccessRequestResponse:
    if not await user_identity_provider.is_internal():
        return TamAccessRequestResponse(
            response="This endpoint is not available for customers."
        )

    start_date, end_date = rbac_core.get_start_end_date_from_duration(
        query_args.duration
    )
    roles = await rbac_core.get_roles_for_tam()
    ok = await rbac_core.send_rbac_tam_request(
        query_args.account_id, query_args.org_id, start_date, end_date, roles
    )

    return TamAccessRequestResponse(
        response=await render_template(
            "platform/rbac/tam_access_request.txt.jinja",
            ok=ok,
            account_id=query_args.account_id,
        )
    )


@blueprint.get("/org-id")
@validate_response(OrgIdResponse)
@document_headers(RHSessionIdHeader)
async def get_org_id(
    user_identity_provider: injector.Inject[AbstractUserIdentityProvider],
    rbac_core: injector.Inject[RBACCore],
) -> OrgIdResponse:
    user_identity = decoded_identity_header(
        await user_identity_provider.get_user_identity()
    )

    return OrgIdResponse(
        response=await render_template(
            "platform/rbac/what_is_my_org_id.txt.jinja",
            org_id=user_identity["identity"]["org_id"],
        )
    )
