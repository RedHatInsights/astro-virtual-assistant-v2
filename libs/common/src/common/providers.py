from typing import Optional

import aiohttp
from injector import Inject, CallableT, provider
from redis.asyncio import StrictRedis

from common.platform_request import (
    DevPlatformRequest,
    ServiceAccountPlatformRequest,
    PlatformRequest,
)
from common.session_storage.file import FileSessionStorage
from common.session_storage.redis import RedisSessionStorage


def make_dev_platform_request_provider(
    refresh_token: str, refresh_token_url: str
) -> CallableT:
    @provider
    def dev_platform_request(
        session: Inject[aiohttp.ClientSession],
    ) -> DevPlatformRequest:
        return DevPlatformRequest(
            session,
            refresh_token=refresh_token,
            refresh_token_url=refresh_token_url,
        )

    return dev_platform_request


def make_sa_platform_request_provider(
    token_url: str, sa_id: str, sa_secret: str
) -> CallableT:
    @provider
    def sa_platform_request(
        session: Inject[aiohttp.ClientSession],
    ) -> ServiceAccountPlatformRequest:
        return ServiceAccountPlatformRequest(
            session,
            token_url=token_url,
            sa_id=sa_id,
            sa_secret=sa_secret,
        )

    return sa_platform_request


def make_platform_request_provider() -> CallableT:
    @provider
    def platform_request(
        session: Inject[aiohttp.ClientSession],
    ) -> PlatformRequest:
        return PlatformRequest(session)

    return platform_request


def make_client_session_provider(proxy: Optional[str]) -> CallableT:
    if proxy is not None and "://" not in proxy:
        proxy = f"http://{proxy}"

    @provider
    def client_session_provider() -> aiohttp.ClientSession:
        return aiohttp.ClientSession(proxy=proxy)

    return client_session_provider


def make_redis_session_storage_provider(hostname: str, port: int) -> CallableT:
    @provider
    def redis_session_storage_provider() -> RedisSessionStorage:
        return RedisSessionStorage(
            StrictRedis(
                host=hostname,
                port=port,
            )
        )

    return redis_session_storage_provider


def make_file_session_storage_provider(file: str) -> CallableT:
    @provider
    def file_session_storage_provider() -> FileSessionStorage:
        return FileSessionStorage(file)

    return file_session_storage_provider
