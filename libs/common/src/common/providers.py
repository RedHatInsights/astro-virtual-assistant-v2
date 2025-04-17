from typing import Optional

import aiohttp
from quart import Quart
from injector import Inject, CallableT, provider
from redis.asyncio import StrictRedis

from common.metrics.quart import get_registry
from common.platform_request import (
    DevPlatformRequest,
    ServiceAccountPlatformRequest,
    PlatformRequest,
    AbstractPlatformRequest,
)
from common.platform_request.tracked_platform_request import TrackedPlatformRequest
from common.session_storage.file import FileSessionStorage
from common.session_storage.redis import RedisSessionStorage


def make_dev_platform_request_provider(
    refresh_token: str, refresh_token_url: str, app_name: str
) -> CallableT:
    @provider
    def dev_platform_request(
        session: Inject[aiohttp.ClientSession], app: Inject[Quart]
    ) -> AbstractPlatformRequest:
        return TrackedPlatformRequest(
            DevPlatformRequest(
                session,
                refresh_token=refresh_token,
                refresh_token_url=refresh_token_url,
            ),
            get_registry(app),
            app_name,
        )

    return dev_platform_request


def make_sa_platform_request_provider(
    token_url: str, sa_id: str, sa_secret: str, app_name: str
) -> CallableT:
    @provider
    def sa_platform_request(
        session: Inject[aiohttp.ClientSession],
        app: Inject[Quart],
    ) -> AbstractPlatformRequest:
        return TrackedPlatformRequest(
            ServiceAccountPlatformRequest(
                session,
                token_url=token_url,
                sa_id=sa_id,
                sa_secret=sa_secret,
            ),
            get_registry(app),
            app_name,
        )

    return sa_platform_request


def make_platform_request_provider(app_name: str) -> CallableT:
    @provider
    def platform_request(
        session: Inject[aiohttp.ClientSession],
        app: Inject[Quart],
    ) -> AbstractPlatformRequest:
        return TrackedPlatformRequest(
            PlatformRequest(session), get_registry(app), app_name
        )

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
