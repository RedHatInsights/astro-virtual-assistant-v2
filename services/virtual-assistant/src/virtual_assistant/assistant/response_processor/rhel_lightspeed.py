from typing import List

import aiohttp
from pydantic import BaseModel

from virtual_assistant.assistant import Response, ResponseType, Query, ResponseText
from virtual_assistant.assistant.response_processor.response_processor import (
    ResponseProcessor,
)

RHEL_LIGHTSPEED_COMMAND = "lightspeed"
RHEL_LIGHTSPEED_PARAM = "rhel"


class RhelLightspeedData(BaseModel):
    model_id: str
    text: str
    # There is also sources - lets explore that by separate


class RhelLightspeedResponse(BaseModel):
    data: RhelLightspeedData


def is_lightspeed_command(response: Response, command: str, arg: str):
    return (
        response.type == ResponseType.COMMAND
        and response.command == command
        and len(response.args) == 1
        and response.args[0] == arg
    )


class RhelLightspeed(ResponseProcessor):
    def __init__(self, session: aiohttp.ClientSession, lightspeed_url: str):
        self.session = session
        self.lightspeed_url = lightspeed_url

    async def lightspeed_query(self, query: Query) -> List[Response]:
        result = await self.session.post(
            f"{self.lightspeed_url}/infer",
            json={
                "question": query.text,
            },
        )

        result.raise_for_status()
        response = RhelLightspeedResponse.model_validate(await result.json())

        return [ResponseText(text=response.data.text)]

    async def process(self, responses: List[Response], query: Query) -> List[Response]:
        result: List[Response] = []
        for response in responses:
            if is_lightspeed_command(
                response, RHEL_LIGHTSPEED_COMMAND, RHEL_LIGHTSPEED_PARAM
            ):
                result.append(*await self.lightspeed_query(query))
            else:
                result.append(response)

        return result
