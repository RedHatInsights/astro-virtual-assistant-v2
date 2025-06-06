import abc
import injector
from typing import Dict, Tuple, Optional, List
from aiohttp import ClientResponse

from watson_extension.clients import SourcesURL
from watson_extension.clients.identity import AbstractUserIdentityProvider
from watson_extension.clients.platform_request import AbstractPlatformRequest
from watson_extension.clients.platform import IntegrationInfo


class SourcesClient(abc.ABC):
    @abc.abstractmethod
    async def get_sources(
        self,
        search: Optional[str] = None,
        enabled: Optional[bool] = None,
        max_integration_num: int = 5,
    ) -> Tuple[bool, Dict]: ...

    @abc.abstractmethod
    async def is_source_name_valid(self, integration_setup_name: str) -> bool: ...

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

    @abc.abstractmethod
    async def sources_update_integration(
        self, integration_id: str, integration_data: Dict
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

    async def get_sources(
        self,
        search: Optional[str] = None,
        enabled: Optional[bool] = None,
        max_integration_num: int = 5,
    ) -> Tuple[bool, List[IntegrationInfo]]:
        sources_search = search or ""

        params = {
            "filter[name][contains_i]": sources_search,
            "limit": max_integration_num,
        }

        if enabled is not None:
            if enabled is True:
                params["filter[paused_at][nil]"] = "1"
            else:
                params["filter[paused_at][not_nil]"] = "1"

        request = "/api/sources/v3.1/sources"
        response = await self.platform_request.get(
            self.sources_url,
            request,
            params=params,
            user_identity=await self.user_identity_provider.get_user_identity(),
        )

        if response.ok:
            content = await response.json()

            sources_integrations = []
            for integration in content["data"]:
                integration_enabled = (
                    True
                    if "paused_at" not in integration
                    or integration["paused_at"] is None
                    else False
                )
                sources_integrations.append(
                    IntegrationInfo(
                        name=integration["name"],
                        enabled=integration_enabled,
                        type="red_hat",
                        group="red_hat",
                        id=integration["id"],
                    )
                )
            return True, sources_integrations

        return False, []

    async def is_source_name_valid(self, integration_setup_name: str) -> bool:
        request = "/api/sources/v3.1/graphql"
        response = await self.platform_request.post(
            self.sources_url,
            request,
            json={
                "query": f'{{ sources(filter: {{name: "name", value: "{integration_setup_name}"}}){{ id, name }}}}'
            },
            user_identity=await self.user_identity_provider.get_user_identity(),
        )

        if response.ok:
            content = await response.json()
            if len(content.get("data").get("sources")) == 0:
                return True

        return False

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
            self.sources_url,
            request,
            json=request_json,
            user_identity=await self.user_identity_provider.get_user_identity(),
        )

        return bool(response.ok)

    async def sources_pause_integration(self, integration_id: str) -> ClientResponse:
        request = f"/api/sources/v3.1/sources/{integration_id}/pause"

        return await self.platform_request.post(
            self.sources_url,
            request,
            user_identity=await self.user_identity_provider.get_user_identity(),
        )

    async def sources_unpause_integration(self, integration_id: str) -> ClientResponse:
        request = f"/api/sources/v3.1/sources/{integration_id}/unpause"

        return await self.platform_request.post(
            self.sources_url,
            request,
            user_identity=await self.user_identity_provider.get_user_identity(),
        )

    async def sources_delete_integration(self, integration_id: str) -> ClientResponse:
        request = f"/api/sources/v3.1/sources/{integration_id}"

        return await self.platform_request.delete(
            self.sources_url,
            request,
            user_identity=await self.user_identity_provider.get_user_identity(),
        )

    async def sources_update_integration(
        self, integration_id: str, integration_data: Dict
    ) -> ClientResponse:
        request = f"/api/sources/v3.1/sources/{integration_id}"

        return await self.platform_request.patch(
            self.sources_url,
            request,
            user_identity=await self.user_identity_provider.get_user_identity(),
            json=integration_data,
        )
