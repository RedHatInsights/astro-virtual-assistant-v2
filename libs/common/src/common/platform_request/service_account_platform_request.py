from typing import Optional

from aiohttp import ClientResponse, ClientSession

from common.platform_request.abstract_platform_request import AbstractPlatformRequest


class ServiceAccountPlatformRequest(AbstractPlatformRequest):
    def __init__(
        self, session: ClientSession, token_url: str, sa_id: str, sa_secret: str
    ):
        super().__init__()
        self.session = session
        self._token_url = token_url
        self._sa_id = sa_id
        self._sa_secret = sa_secret
        self._token = None

    async def refresh_token(self):
        response = await self.session.post(
            self._token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": self._sa_id,
                "client_secret": self._sa_secret,
            },
        )

        response.raise_for_status()

        content = await response.json()
        self._token = content["access_token"]

    async def request(
        self,
        method: str,
        base_url: str,
        api_path: str,
        user_identity: Optional[str] = None,
        **kwargs,
    ) -> ClientResponse:
        # We could check if we have a token... or if it is expired.
        await self.refresh_token()

        headers = kwargs.pop("headers", {})
        if user_identity is not None:
            headers["Authorization"] = "Bearer " + self._token

        return await self.session.request(
            method, f"{base_url}{api_path}", headers=headers, **kwargs
        )
