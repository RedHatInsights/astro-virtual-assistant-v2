import injector
from pydantic import BaseModel

from quart import Blueprint
from quart_schema import validate_querystring, document_headers, validate_response

from common.auth import decoded_identity_header

from watson_extension.clients.identity import AbstractUserIdentityProvider
from watson_extension.core.insights.notifications import (
    NotificationsCore,
)
from watson_extension.routes import RHSessionIdHeader

blueprint = Blueprint("notifications", __name__, url_prefix="/notifications")


class RbacRequestAdminEmail(BaseModel):
    user_message: str
    requested_url: str


class ResponseSendRbacRequestAdminEmail(BaseModel):
    response: str = ""


@blueprint.post("/send_rbac_request_admin_email")
@validate_querystring(RbacRequestAdminEmail)
@validate_response(ResponseSendRbacRequestAdminEmail)
@document_headers(RHSessionIdHeader)
async def send_rbac_request_admi_email(
    query_args: RbacRequestAdminEmail,
    user_identity_provider: injector.Inject[AbstractUserIdentityProvider],
    notifications_service: injector.Inject[NotificationsCore],
) -> ResponseSendRbacRequestAdminEmail:
    user_identity = decoded_identity_header(
        await user_identity_provider.get_user_identity()
    )

    org_id = user_identity["identity"]["org_id"]
    username = user_identity["identity"]["user"]["username"]
    user_email = user_identity["identity"]["user"]["email"]

    await notifications_service.send_rbac_request_admin(
        org_id=org_id,
        username=username,
        user_email=user_email,
        user_message=query_args.user_message,
        requested_url=query_args.requested_url,
    )
    return ResponseSendRbacRequestAdminEmail()
