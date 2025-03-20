import abc
from typing import List

from virtual_assistant.assistant import Response, Query


class ResponseProcessor(abc.ABC):
    @abc.abstractmethod
    async def process(self, responses: List[Response], query: Query):
        List[Response]: ...
