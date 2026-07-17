import injector
from common.auth import decoded_identity_header
from common.security_log import get_principal_from_identity, security_log
from pydantic import BaseModel
from quart import Blueprint, render_template
from quart_schema import document_headers, validate_querystring, validate_response

from watson_extension.clients.identity import AbstractUserIdentityProvider
from watson_extension.core.platform.rbac import (
    RBACCore,
)
from watson_extension.routes import RHSessionIdHeader

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
    user_identity = await user_identity_provider.get_user_identity()
    principal = get_principal_from_identity(user_identity)

    if not await user_identity_provider.is_internal():
        security_log(
            action="AUTHZ_FAILURE",
            resource_type="tam_access_request",
            resource_id=query_args.account_id,
            outcome="failure",
            principal=principal,
            reason="non-internal user attempted TAM access",
        )
        return TamAccessRequestResponse(response="This endpoint is not available for customers.")

    start_date, end_date = rbac_core.get_start_end_date_from_duration(query_args.duration)
    roles = await rbac_core.get_roles_for_tam()
    ok = await rbac_core.send_rbac_tam_request(query_args.account_id, query_args.org_id, start_date, end_date, roles)

    security_log(
        action="CREATE",
        resource_type="tam_access_request",
        resource_id=query_args.account_id,
        outcome="success" if ok else "failure",
        principal=principal,
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
    user_identity = decoded_identity_header(await user_identity_provider.get_user_identity())

    return OrgIdResponse(
        response=await render_template(
            "platform/rbac/what_is_my_org_id.txt.jinja",
            org_id=user_identity["identity"]["org_id"],
        )
    )
