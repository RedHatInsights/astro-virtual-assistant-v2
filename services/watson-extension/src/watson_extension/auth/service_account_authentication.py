import base64
import binascii
import json

import quart
from common.security_log import get_principal_from_identity, security_log
from werkzeug.exceptions import Unauthorized

from watson_extension.auth import Authentication


class ServiceAccountAuthentication(Authentication):
    def __init__(self, client_id: str):
        self.client_id = client_id

    async def check_auth(self, request: quart.Request):
        identity_header = request.headers.get("x-rh-identity")
        if not identity_header:
            security_log(
                action="AUTH_FAILURE",
                resource_type="identity",
                resource_id=request.path,
                outcome="failure",
                principal={"type": "anonymous"},
                reason="missing identity header",
            )
            raise Unauthorized("Missing identity header")

        try:
            decoded = json.loads(base64.b64decode(identity_header))
        except (binascii.Error, ValueError):
            security_log(
                action="AUTH_FAILURE",
                resource_type="identity",
                resource_id=request.path,
                outcome="failure",
                principal={"type": "anonymous"},
                reason="invalid identity header encoding",
            )
            raise Unauthorized("Invalid identity header") from None

        if "identity" not in decoded or "service_account" not in decoded["identity"]:
            security_log(
                action="AUTH_FAILURE",
                resource_type="identity",
                resource_id=request.path,
                outcome="failure",
                principal=get_principal_from_identity(identity_header),
                reason="not a service account identity",
            )
            raise Unauthorized("Invalid identity header")

        service_account = decoded["identity"]["service_account"]

        if service_account["client_id"] != self.client_id:
            security_log(
                action="AUTH_FAILURE",
                resource_type="identity",
                resource_id=request.path,
                outcome="failure",
                principal=get_principal_from_identity(identity_header),
                reason="service account client_id mismatch",
            )
            raise Unauthorized("Invalid identity header")
