from typing import Optional, Dict, List
import abc
import injector
import logging
from aiohttp import ClientResponse
from watson_extension.clients import PlatformNotificationsURL
from watson_extension.clients.identity import AbstractUserIdentityProvider
from watson_extension.clients.platform_request import AbstractPlatformRequest


logger = logging.getLogger(__name__)


class PlatformNotificationsClient(abc.ABC):
    @abc.abstractmethod
    async def get_available_bundles(self): ...


class PlatformNotificationsClientHttp(PlatformNotificationsClient):
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

    async def get_available_bundles(self) -> Dict:
        params = {
            "includeApplications": "false",
        }

        response = await self.platform_request.get(
            self.platform_notifications_url,
            "/api/notifications/v1.0/notifications/facets/bundles",
            params=params,
        )

        response.raise_for_status()

        return response.json()

    async def get_available_events_by_bundle(
        self, bundleId: str, exclude_muted_types: Optional[bool] = False
    ) -> Dict:
        params = {
            "limit": 20,
            "offset": 0,
            "sort_by": "application:ASC",
            "bundleId": bundleId,
            "excludeMutedTypes": str(exclude_muted_types),
        }
        response = await self.platform_request.get(
            self.platform_notifications_url,
            "/api/notifications/v1.0/notifications/eventTypes",
            params=params,
        )

        response.raise_for_status()

        return response.json()

    async def get_behavior_groups(self, bundleId: str) -> List:
        response = await self.platform_request.get(
            self.platform_notifications_url,
            f"/api/notifications/v1.0/notifications/bundles/{bundleId}/behaviorGroups",
        )

        response.raise_for_status()

        return response.json()

    async def mute_event(self, eventId: str) -> ClientResponse:
        headers = {"Content-Type": "application/json"}

        return await self.platform_request.put(
            self.platform_notifications_url,
            f"/api/notifications/v1.0/notifications/eventTypes/{eventId}/behaviorGroups",
            "put",
            json=[],
            headers=headers,
        )
