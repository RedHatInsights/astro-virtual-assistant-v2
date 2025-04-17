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
    is_group: bool = False
    is_external: bool = False
    href: Optional[str] = None


@dataclass
class Service:
    description: str
    id: str
    links: Optional[List[dict]]
    title: str
    href: Optional[str]


class ChromeServiceClient(abc.ABC):
    @abc.abstractmethod
    async def get_user(self) -> User: ...

    @abc.abstractmethod
    async def get_generated_services(self) -> List[Service]: ...

    @abc.abstractmethod
    async def modify_favorite_service(
        self, service, favorite=True
    ) -> List[Favorite]: ...


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
        response = await self.platform_request.get(
            self.chrome_url,
            "/api/chrome-service/v1/user",
            user_identity=await self.user_identity_provider.get_user_identity(),
        )
        response.raise_for_status()

        data = json.loads(await response.text())["data"]
        return User(
            account_id=data["accountId"],
            first_login=data["firstLogin"],
            day_one=data["dayOne"],
            last_login=data["lastLogin"],
            last_visited_pages=data["lastVisitedPages"],
            favorite_pages=[
                Favorite(
                    id=fp["id"],
                    pathname=fp["pathname"],
                    favorite=fp["favorite"],
                    user_identity_id=fp["userIdentityId"],
                )
                for fp in data.get("favoritePages", [])
            ],
            visited_bundles=data.get("visitedBundles", {}),
        )

    async def get_generated_services(self) -> List[Service]:
        response = await self.platform_request.get(
            self.chrome_url,
            "/api/chrome-service/v1/static/stable/prod/services/services-generated.json",
            user_identity=await self.user_identity_provider.get_user_identity(),
        )
        response.raise_for_status()

        data = await response.json()
        return [
            Service(
                description=service.get("description", ""),
                id=service.get("id", ""),
                links=parse_links_into_obj(service.get("links", [])),
                title=service.get("title", ""),
                href=service.get("href", ""),
            )
            for service in data
        ]

    async def modify_favorite_service(self, href, favorite=True):
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
        return await response.text()


def parse_links_into_obj(links) -> List[Link]:
    if not links:
        return []
    parsed_links = []
    for link in links:
        parsed_links.append(
            Link(
                id=link.get("id"),
                title=link.get("title", ""),
                alt_title=link.get("altTitle", []),
                links=parse_links_into_obj(link.get("links", [])),
                app_id=link.get("appId"),
                is_group=link.get("isGroup", False),
                is_external=link.get("isExternal", False),
                href=link.get("href", ""),
            )
        )
    return parsed_links
