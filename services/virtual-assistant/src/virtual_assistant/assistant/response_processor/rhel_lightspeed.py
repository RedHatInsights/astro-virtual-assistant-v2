from typing import List

from pydantic import BaseModel

from common.identity import AbstractUserIdentityProvider
from common.platform_request import AbstractPlatformRequest
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
    def __init__(
        self,
        lightspeed_url: str,
        user_identity_provider: AbstractUserIdentityProvider,
        platform_request: AbstractPlatformRequest,
    ):
        self.platform_request = platform_request
        self.lightspeed_url = lightspeed_url
        self.user_identity_provider = user_identity_provider

    async def lightspeed_query(self, query: Query) -> List[Response]:
        result = await self.platform_request.post(
            self.lightspeed_url,
            "/api/lightspeed/v1/infer",
            json={
                "question": query.text,
            },
            user_identity=await self.user_identity_provider.get_user_identity(),
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
