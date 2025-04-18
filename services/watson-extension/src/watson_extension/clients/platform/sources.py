import abc
import injector
from typing import Dict, Tuple
from aiohttp import ClientResponse

from watson_extension.clients import SourcesURL
from watson_extension.clients.identity import AbstractUserIdentityProvider
from watson_extension.clients.platform_request import AbstractPlatformRequest


class SourcesClient(abc.ABC):
    @abc.abstractmethod
    async def get_sources(self, params: Dict) -> Tuple[bool, Dict]: ...

    @abc.abstractmethod
    async def bulk_create(
        self,
        integration_setup_name: str,
        integration_setup_redhat_cluster_identifier: str,
    ) -> bool: ...

    @abc.abstractmethod
    async def sources_pause_integration(
        self, integration_id: str
    ) -> ClientResponse: ...

    @abc.abstractmethod
    async def sources_unpause_integration(
        self, integration_id: str
    ) -> ClientResponse: ...

    @abc.abstractmethod
    async def sources_delete_integration(
        self, integration_id: str
    ) -> ClientResponse: ...


class SourcesClientHttp(SourcesClient):
    def __init__(
        self,
        sources_url: injector.Inject[SourcesURL],
        user_identity_provider: injector.Inject[AbstractUserIdentityProvider],
        platform_request: injector.Inject[AbstractPlatformRequest],
    ):
        super().__init__()
        self.sources_url = sources_url
        self.user_identity_provider = user_identity_provider
        self.platform_request = platform_request

    async def get_sources(self, params: Dict) -> Tuple[bool, Dict]:
        request = "/api/sources/v3.1/sources"
        response = await self.platform_request.get(
            self.sources_url, request, params=params
        )

        if response.ok:
            content = await response.json()
            return False, content

        return True, {}

    async def bulk_create(
        self,
        integration_setup_name: str,
        integration_setup_redhat_cluster_identifier: str,
    ) -> bool:
        request = "/api/sources/v3.1/bulk_create"
        request_json = {
            "applications": [
                {
                    "application_type_id": "2",
                    "extra": {"hcs": False},
                    "source_name": integration_setup_name,
                }
            ],
            "authentications": [
                {
                    "authtype": "token",
                    "resource_name": "/insights/platform/cost-management",
                    "resource_type": "application",
                }
            ],
            "endpoints": [],
            "sources": [
                {
                    "name": integration_setup_name,
                    "source_ref": integration_setup_redhat_cluster_identifier,
                    "source_type_name": "openshift",
                }
            ],
        }

        response = await self.platform_request.post(
            self.sources_url, request, json=request_json
        )

        if response.ok:
            return True

        return False

    async def sources_pause_integration(self, integration_id: str) -> ClientResponse:
        request = f"/api/sources/v3.1/sources/{integration_id}/pause"

        return await self.platform_request.post(self.sources_url, request)

    async def sources_unpause_integration(self, integration_id: str) -> ClientResponse:
        request = f"/api/sources/v3.1/sources/{integration_id}/unpause"

        return await self.platform_request.post(self.sources_url, request)

    async def sources_delete_integration(self, integration_id: str) -> ClientResponse:
        request = f"/api/sources/v3.1/sources/{integration_id}"

        return await self.platform_request.delete(self.sources_url, request)
