import abc
from typing import Optional
from aiohttp import ClientResponse

from aiohttp.hdrs import (
    METH_GET,
    METH_OPTIONS,
    METH_HEAD,
    METH_POST,
    METH_PUT,
    METH_PATCH,
    METH_DELETE,
)


class AbstractPlatformRequest(abc.ABC):
    @abc.abstractmethod
    async def request(
        self,
        method: str,
        base_url: str,
        api_path: str,
        user_identity: Optional[str] = None,
        **kwargs,
    ) -> ClientResponse: ...

    async def get(
        self,
        base_url: str,
        api_path: str,
        user_identity: Optional[str] = None,
        **kwargs,
    ) -> ClientResponse:
        return await self.request(METH_GET, base_url, api_path, user_identity, **kwargs)

    async def options(
        self,
        base_url: str,
        api_path: str,
        user_identity: Optional[str] = None,
        **kwargs,
    ) -> ClientResponse:
        return await self.request(
            METH_OPTIONS, base_url, api_path, user_identity, **kwargs
        )

    async def head(
        self,
        base_url: str,
        api_path: str,
        user_identity: Optional[str] = None,
        **kwargs,
    ) -> ClientResponse:
        return await self.request(
            METH_HEAD, base_url, api_path, user_identity, **kwargs
        )

    async def post(
        self,
        base_url: str,
        api_path: str,
        user_identity: Optional[str] = None,
        **kwargs,
    ) -> ClientResponse:
        return await self.request(
            METH_POST, base_url, api_path, user_identity, **kwargs
        )

    async def put(
        self,
        base_url: str,
        api_path: str,
        user_identity: Optional[str] = None,
        **kwargs,
    ) -> ClientResponse:
        return await self.request(METH_PUT, base_url, api_path, user_identity, **kwargs)

    async def patch(
        self,
        base_url: str,
        api_path: str,
        user_identity: Optional[str] = None,
        **kwargs,
    ) -> ClientResponse:
        return await self.request(
            METH_PATCH, base_url, api_path, user_identity, **kwargs
        )

    async def delete(
        self,
        base_url: str,
        api_path: str,
        user_identity: Optional[str] = None,
        **kwargs,
    ) -> ClientResponse:
        return await self.request(
            METH_DELETE, base_url, api_path, user_identity, **kwargs
        )
