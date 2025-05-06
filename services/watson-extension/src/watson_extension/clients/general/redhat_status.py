import abc
import logging
from typing import Optional, Dict
import injector
import aiohttp


logger = logging.getLogger(__name__)


class RedhatStatusClient(abc.ABC):
    @abc.abstractmethod
    async def check_services_offline(self) -> Optional[Dict]: ...


class RedhatStatusClientHttp(RedhatStatusClient):
    def __init__(self, session: injector.Inject[aiohttp.ClientSession]):
        super().__init__()
        self.session = session

    async def check_services_offline(self) -> Optional[Dict]:
        result = None
        try:
            async with self.session.get(
                "https://status.redhat.com/api/v2/incidents/unresolved.json", ssl=False
            ) as status_response:
                result = await status_response.json()
        except Exception as e:
            logger.error(
                f"An Exception occured while handling response from status.redhat.com: {e}"
            )
            raise e
        return result
