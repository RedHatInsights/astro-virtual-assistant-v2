from typing import Optional, Tuple, List, Dict
import abc
import injector
import logging
import enum
from urllib.parse import urlparse
from aiohttp import ClientResponse
from watson_extension.clients import PlatformNotificationsURL
from watson_extension.clients.identity import AbstractUserIdentityProvider
from watson_extension.clients.platform_request import AbstractPlatformRequest
from watson_extension.clients.platform import IntegrationInfo


logger = logging.getLogger(__name__)


reporting_types = ["ansible"]
communications_camel_subtypes = ["google_chat", "teams", "slack"]
reporting_camel_subtypes = ["servicenow", "splunk"]
MAX_NUMBER_OF_INTEGRATIONS = 5


class CreateEndpointResponseType(enum.Enum):
    OK = "ok"
    NOT_HTTPS = "not_https"
    ATTRIBUTION_ERROR = "attribution_error"


async def validate_integration_url(
    integrations_setup_url: str,
) -> CreateEndpointResponseType:
    try:
        result = urlparse(integrations_setup_url)
        if result.scheme != "https":
            return CreateEndpointResponseType.NOT_HTTPS
    except AttributeError:
        return CreateEndpointResponseType.ATTRIBUTION_ERROR

    return CreateEndpointResponseType.OK


def notifications_type_to_group(integration: Dict) -> str:
    if integration["type"] == "webhook":
        return "webhook"
    if integration["type"] in reporting_types:
        return "reporting"

    if integration["type"] == "camel":
        if integration["sub_type"] in communications_camel_subtypes:
            return "communications"
        if integration["sub_type"] in reporting_camel_subtypes:
            return "reporting"


class IntegrationsClient(abc.ABC):
    @abc.abstractmethod
    async def create_endpoint(
        self,
        setup_name: str,
        setup_url: str,
        secret_token: str,
        setup_type: str,
        setup_sub_type: Optional[str] = None,
    ) -> bool: ...

    @abc.abstractmethod
    async def fetch_integrations(
        self, search: Optional[str] = None, enabled: Optional[bool] = None
    ) -> Tuple[bool, Optional[List[IntegrationInfo]]]: ...

    @abc.abstractmethod
    async def integration_resume(self, integration_id: str) -> ClientResponse: ...

    @abc.abstractmethod
    async def integration_pause(self, integration_id: str) -> ClientResponse: ...

    @abc.abstractmethod
    async def delete_integration(self, integration_id: str) -> ClientResponse: ...

    @abc.abstractmethod
    async def retrieve_notification_endpoint(
        self, endpoint_id: str
    ) -> ClientResponse: ...

    @abc.abstractmethod
    async def update_integration(
        self, integration_id: str, integration_data: Dict
    ) -> ClientResponse: ...


class IntegrationsClientHttp(IntegrationsClient):
    def __init__(
        self,
        platform_notifications_url: injector.Inject[PlatformNotificationsURL],
        user_identity_provider: injector.Inject[AbstractUserIdentityProvider],
        platform_request: injector.Inject[AbstractPlatformRequest],
    ):
        super().__init__()
        self.platform_notifications_url = platform_notifications_url
        self.user_identity_provider = user_identity_provider
        self.platform_request = platform_request

    async def create_endpoint(
        self,
        setup_name: str,
        setup_url: str,
        setup_type: str,
        setup_sub_type: Optional[str] = None,
        secret_token: Optional[str] = None,
    ) -> bool:
        request = "/api/integrations/v1.0/endpoints"
        response = await self.platform_request.post(
            self.platform_notifications_url,
            request,
            user_identity=await self.user_identity_provider.get_user_identity(),
            json={
                "enabled": True,
                "description": "Endpoint created by Virtual assistant",
                "name": setup_name,
                "properties": {
                    "method": "POST",
                    "disable_ssl_verification": False,
                    "url": setup_url,
                    "secret_token": secret_token,
                },
                "type": setup_type,
                "sub_type": setup_sub_type,
            },
        )

        return bool(response.ok)

    async def fetch_integrations(
        self, search: Optional[str] = None, enabled: Optional[bool] = None
    ) -> Tuple[bool, Optional[List[IntegrationInfo]]]:
        integration_search = search or ""

        prepend_camel = lambda s: f"camel:{s}"  # noqa: E731

        params = {
            "name": integration_search,
            "type": [
                "webhook",
                *reporting_types,
                *map(prepend_camel, reporting_camel_subtypes),
                *map(prepend_camel, communications_camel_subtypes),
            ],
            "limit": MAX_NUMBER_OF_INTEGRATIONS,
        }

        if enabled is not None:
            params["active"] = str(enabled)

        request = "/api/integrations/v1.0/endpoints"
        response = await self.platform_request.get(
            self.platform_notifications_url,
            request,
            params=params,
            user_identity=await self.user_identity_provider.get_user_identity(),
        )

        if response.ok:
            content = await response.json()

            integrations = []
            for integration in content["data"]:
                integrations.append(
                    IntegrationInfo(
                        name=integration["name"],
                        enabled=integration["enabled"],
                        type="notifications",
                        group=notifications_type_to_group(integration),
                        id=integration["id"],
                    )
                )

            return False, integrations

        return True, None

    async def integration_resume(self, integration_id: str) -> ClientResponse:
        request = f"/api/integrations/v1.0/endpoints/{integration_id}/enable"
        return await self.platform_request.put(
            self.platform_notifications_url,
            request,
            user_identity=await self.user_identity_provider.get_user_identity(),
        )

    async def integration_pause(self, integration_id: str) -> ClientResponse:
        request = f"/api/integrations/v1.0/endpoints/{integration_id}/enable"
        return await self.platform_request.delete(
            self.platform_notifications_url,
            request,
            user_identity=await self.user_identity_provider.get_user_identity(),
        )

    async def delete_integration(self, integration_id: str) -> ClientResponse:
        request = f"/api/integrations/v1.0/endpoints/{integration_id}"
        return await self.platform_request.delete(
            self.platform_notifications_url,
            request,
            user_identity=await self.user_identity_provider.get_user_identity(),
        )

    async def retrieve_notification_endpoint(self, endpoint_id: str) -> ClientResponse:
        request = f"/api/integrations/v1.0/endpoints/{endpoint_id}"
        return await self.platform_request.get(
            self.platform_notifications_url,
            request,
            user_identity=await self.user_identity_provider.get_user_identity(),
        )

    async def update_integration(
        self, integration_id: str, integration_data: Dict
    ) -> ClientResponse:
        request = f"/api/integrations/v1.0/endpoints/{integration_id}"
        return await self.platform_request.put(
            self.platform_notifications_url,
            request,
            json=integration_data,
            user_identity=await self.user_identity_provider.get_user_identity(),
        )
