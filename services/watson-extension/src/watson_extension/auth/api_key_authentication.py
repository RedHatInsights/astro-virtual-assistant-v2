from typing import List

import quart
from common.security_log import security_log
from werkzeug.exceptions import Unauthorized

from watson_extension.auth import Authentication


class ApiKeyAuthentication(Authentication):
    def __init__(self, valid_keys: List[str]):
        self.valid_keys = valid_keys

    async def check_auth(self, request: quart.Request):
        api_key = request.args.get("api_key")
        if api_key not in self.valid_keys:
            security_log(
                action="AUTH_FAILURE",
                resource_type="api_key",
                resource_id=request.path,
                outcome="failure",
                principal={"type": "anonymous"},
                reason="invalid api_key",
            )
            raise Unauthorized("Invalid api_key")
