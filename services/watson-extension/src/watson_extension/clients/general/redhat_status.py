import abc
import logging
from aiohttp import ClientResponse, ClientSession


logger = logging.getLogger(__name__)


class RedhatStatusClient(abc.ABC):
    @abc.abstractmethod
    async def check_services_offline(self) -> ClientResponse: ...


class RedhatStatusClientHttp(RedhatStatusClient):
    def __init__(
        self,
    ):
        super().__init__()

    async def check_services_offline(self) -> ClientResponse:
        try:
            async with ClientSession() as session:
                async with session.get(
                    "https://status.redhat.com/api/v2/incidents/unresolved.json"
                ) as status_response:
                    result = await status_response.json()
        except Exception as e:
            print(
                f"An Exception occured while handling response from status.redhat.com: {e}"
            )
        return result
