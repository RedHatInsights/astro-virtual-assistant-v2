import abc
import logging
from typing import Optional, Dict
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

    async def check_services_offline(self) -> Optional[Dict]:
        result = None
        try:
            async with ClientSession(trust_env=True) as session:
                async with session.get(
                    "https://status.redhat.com/api/v2/incidents/unresolved.json"
                ) as status_response:
                    result = await status_response.json()
        except Exception as e:
            logger.error(
                f"An Exception occured while handling response from status.redhat.com: {e}"
            )
            raise e
        return result
