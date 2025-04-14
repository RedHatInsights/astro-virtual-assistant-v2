import abc
import json
import injector
from dataclasses import dataclass
from typing import List, Optional

from common.identity import AbstractUserIdentityProvider
from common.platform_request import AbstractPlatformRequest
from watson_extension.clients import ChromeServiceURL


@dataclass
class Favorite:
    id: str
    pathname: str
    favorite: bool
    user_identity_id: str


@dataclass
class User:
    account_id: str
    first_login: bool
    day_one: bool
    last_login: str
    last_visited_pages: List[dict]
    favorite_pages: List[Favorite]
    visited_bundles: dict


@dataclass
class Link:
    id: Optional[str]
    title: str
    alt_title: Optional[List[str]]
    links: Optional["Link"]
    app_id: Optional[str] = None
    is_group: Optional[bool] = None
    is_external: Optional[bool] = None
    href: Optional[str] = None

@dataclass
class Service:
    description: str
    id: str
    links: List[dict]
    title: str
    href: str
    group: str


class ChromeServiceClient(abc.ABC):
    @abc.abstractmethod
    async def get_user(self) -> User: ...

    @abc.abstractmethod
    async def get_generated_services(self) -> List[Service]: ...

    @abc.abstractmethod
    async def modify_favorite_service(self, service, favorite=True) -> List[Favorite]: ...


class ChromeServiceClientHttp(ChromeServiceClient):
    def __init__(
        self,
        chrome_url: injector.Inject[ChromeServiceURL],
        user_identity_provider: injector.Inject[AbstractUserIdentityProvider],
        platform_request: injector.Inject[AbstractPlatformRequest],
    ):
        super().__init__()
        self.chrome_url = chrome_url
        self.user_identity_provider = user_identity_provider
        self.platform_request = platform_request


    async def get_user(self):
        # struggles to be a json response, manually doing it here
        response, content = await self.platform_request.get(
            self.chrome_url,
            "/api/chrome-service/v1/user",
            user_identity=await self.user_identity_provider.get_user_identity()
        )
        response.raise_for_status()

        return json.loads(response.content)
    
    async def get_generated_services(self):
        return await self.platform_request.get(
            self.chrome_url,
            "/api/chrome-service/v1/static/stable/prod/services/services-generated.json",
            user_identity=await self.user_identity_provider.get_user_identity()
        )

    async def modify_favorite_service(self, href, favorite=True) -> List[Favorite]:
        response = await self.platform_request.post(
            self.chrome_url,
            "/api/chrome-service/v1/favorite-pages",
            user_identity=await self.user_identity_provider.get_user_identity(),
            json={
                "favorite": favorite,
                "pathname": href,
            },
        )
        response.raise_for_status()
        return response
