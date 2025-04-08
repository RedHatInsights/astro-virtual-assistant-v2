import abc

import injector
import logging
from watson_extension.clients import NotificationsGWURL
from watson_extension.clients.identity import AbstractUserIdentityProvider
from watson_extension.clients.platform_request import AbstractPlatformRequest


logger = logging.getLogger(__name__)


class NotificationsClient(abc.ABC):
    @abc.abstractmethod
    async def send_notification(self, event: dict): ...


class NotificationsClientHttp(NotificationsClient):
    def __init__(
        self,
        notifications_gw_url: injector.Inject[NotificationsGWURL],
        user_identity_provider: injector.Inject[AbstractUserIdentityProvider],
        platform_request: injector.Inject[AbstractPlatformRequest],
    ):
        super().__init__()
        self.notifications_gw_url = notifications_gw_url
        self.user_identity_provider = user_identity_provider
        self.platform_request = platform_request

    async def send_notification(
        self,
        event: dict,
    ):
        headers = {"Content-Type": "application/json"}

        response = await self.platform_request.post(
            self.notifications_gw_url,
            "/notifications",
            user_identity=await self.user_identity_provider.get_user_identity(),
            json=event,
            headers=headers,
        )

        response.raise_for_status()

        return ""


class NotificationClientNoOp(NotificationsClient):
    async def send_notification(self, event: dict):
        logger.info(event)
        return ""
