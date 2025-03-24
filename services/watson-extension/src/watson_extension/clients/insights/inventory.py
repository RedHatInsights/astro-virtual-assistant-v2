import abc
import enum
from dataclasses import dataclass
from typing import Optional, List

import injector

from watson_extension.clients import RHSMURL
from watson_extension.clients.identity import AbstractUserIdentityProvider
from watson_extension.clients.platform_request import AbstractPlatformRequest


@dataclass
class ActivationKeyResponse:
    ok: bool
    message: Optional[str]


class InventoryClient(abc.ABC):
    @abc.abstractmethod
    async def create_activation_key(self, name: str): ...


class InventoryClientHttp(InventoryClient):
    def __init__(
        self,
        rhsm_url: injector.Inject[RHSMURL],
        user_identity_provider: injector.Inject[AbstractUserIdentityProvider],
        platform_request: injector.Inject[AbstractPlatformRequest],
    ):
        super().__init__()
        self.rhsm_url = rhsm_url
        self.user_identity_provider = user_identity_provider
        self.platform_request = platform_request

    async def create_activation_key(self, name: str):
        body = {"name": name, "role": "", "serviceLevel": "", "usage": ""}
        response = await self.platform_request.post(
            self.rhsm_url,
            "/api/rhsm/v2/activation_keys",
            user_identity=await self.user_identity_provider.get_user_identity(),
            json=body,
        )
        response.raise_for_status()

        response_json = await response.json()

        if not response.ok:
            return ActivationKeyResponse(
                ok=response.ok,
                message=response_json.get("error", {}).get(
                    "message", "Unknown error"
                )
            )
        return ActivationKeyResponse(ok=response.ok, message=None)
