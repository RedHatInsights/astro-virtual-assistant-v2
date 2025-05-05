import abc
import injector
import logging
from aiohttp import ClientResponse
from watson_extension.clients.platform_request import AbstractPlatformRequest


logger = logging.getLogger(__name__)


class RedhatStatusClient(abc.ABC):
    @abc.abstractmethod
    async def check_services_offline(self) -> ClientResponse: ...


class RedhatStatusClientHttp(RedhatStatusClient):
    def __init__(
        self,
        platform_request: injector.Inject[AbstractPlatformRequest],
    ):
        super().__init__()
        self.platform_request = platform_request

    async def check_services_offline(self) -> ClientResponse:
        base_url = "https://status.redhat.com"
        request = "/api/v2/incidents/unresolved.json"
        return await self.platform_request.get(base_url, request)
