from typing import Optional

from common.platform_request.abstract_platform_request import AbstractPlatformRequest

from aiohttp import ClientResponse, ClientSession


class PlatformRequest(AbstractPlatformRequest):
    def __init__(self, session: ClientSession):
        self.session = session

    async def request(
        self,
        method: str,
        base_url: str,
        api_path: str,
        user_identity: Optional[str] = None,
        **kwargs,
    ) -> ClientResponse:
        headers = kwargs.pop("headers", {})
        if user_identity is not None:
            headers["x-rh-identity"] = user_identity

        return await self.session.request(
            method, f"{base_url}{api_path}", headers=headers, **kwargs
        )
