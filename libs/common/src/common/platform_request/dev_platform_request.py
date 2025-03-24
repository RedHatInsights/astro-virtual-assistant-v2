from typing import Optional

from common.platform_request.abstract_platform_request import AbstractPlatformRequest

from werkzeug.exceptions import InternalServerError
from aiohttp import ClientResponse, ClientSession


class DevPlatformRequest(AbstractPlatformRequest):
    def __init__(
        self,
        session: ClientSession,
        refresh_token: str,
        refresh_token_url: str,
    ):
        super().__init__()
        self.session = session
        self._refresh_token = refresh_token
        self._refresh_token_url = refresh_token_url
        self._dev_token: Optional[str] = None

    async def refresh_token(self):
        result = await self.session.post(
            self._refresh_token_url,
            data={
                "grant_type": "refresh_token",
                "client_id": "rhsm-api",
                "refresh_token": self._refresh_token,
            },
        )

        if not result.ok:
            raise InternalServerError("Unable to refresh dev token")
        token = (await result.json())["access_token"]
        self.verify_token(token)
        self._dev_token = token

    @staticmethod
    def verify_token(token: str):
        import jwt

        jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": True, "verify_nbf": True},
        )

    async def request(
        self,
        method: str,
        base_url: str,
        api_path: str,
        user_identity: Optional[str] = None,
        **kwargs,
    ) -> ClientResponse:
        import jwt

        if self._dev_token is not None:
            try:
                self.verify_token(self._dev_token)
            except jwt.InvalidTokenError:
                await self.refresh_token()
        else:
            await self.refresh_token()

        headers = kwargs.pop("headers", {})
        if user_identity is not None:
            headers["Authorization"] = "Bearer " + self._dev_token

        return await self.session.request(
            method, f"{base_url}{api_path}", headers=headers, **kwargs
        )
