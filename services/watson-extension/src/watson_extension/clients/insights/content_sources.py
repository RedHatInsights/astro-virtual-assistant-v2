import abc
from dataclasses import dataclass
from typing import Optional, List

import injector

from watson_extension.clients import ContentSourcesURL
from watson_extension.clients.identity import AbstractUserIdentityProvider
from watson_extension.clients.platform_request import AbstractPlatformRequest


@dataclass
class GetPopularRepositoriesResponse:
    data: Optional[List[dict]]


@dataclass
class BulkCreateRepositoriesInfo:
    suggested_name: str
    distribution_arch: str
    distribution_versions: List[str]
    gpg_key: str
    metadata_verification: bool
    snapshot: bool
    url: str


@dataclass
class RepositoriesBulkCreateResponse:
    response: Optional[str] = None


class ContentSourcesClient(abc.ABC):
    @abc.abstractmethod
    async def get_popular_repositories(self) -> GetPopularRepositoriesResponse: ...

    @abc.abstractmethod
    async def repositories_bulk_create(
        self,
        repository_info: List[BulkCreateRepositoriesInfo],
    ) -> RepositoriesBulkCreateResponse: ...


class ContentSourcesClientHttp(ContentSourcesClient):
    def __init__(
        self,
        content_sources_url: injector.Inject[ContentSourcesURL],
        user_identity_provider: injector.Inject[AbstractUserIdentityProvider],
        platform_request: injector.Inject[AbstractPlatformRequest],
    ):
        super().__init__()
        self.content_sources_url = content_sources_url
        self.user_identity_provider = user_identity_provider
        self.platform_request = platform_request

    async def get_popular_repositories(self) -> GetPopularRepositoriesResponse:
        request = "/api/content-sources/v1/popular_repositories/?offset=0&limit=20"
        response = await self.platform_request.get(
            self.content_sources_url,
            request,
            user_identity=await self.user_identity_provider.get_user_identity(),
        )
        response.raise_for_status()

        content = await response.json()

        return GetPopularRepositoriesResponse(data=content["data"])

    async def repositories_bulk_create(
        self,
        repository_info: List[BulkCreateRepositoriesInfo],
    ) -> RepositoriesBulkCreateResponse:
        headers = {"Content-Type": "application/json"}

        request = "/api/content-sources/v1.0/repositories/bulk_create/"
        response = await self.platform_request.post(
            self.content_sources_url,
            request,
            user_identity=await self.user_identity_provider.get_user_identity(),
            json=repository_info,
            headers=headers,
        )
        status = response.status

        content = await response.json()

        errors = None
        if "errors" in content:
            errors = content["errors"]

        repositories_response = None
        if status >= 400 and any(
            "already belongs" in error["detail"] for error in errors
        ):
            repositories_response = "already_enabled"
        elif status == 201:
            repositories_response = "enabled"
        else:
            repositories_response = "errors"

        return RepositoriesBulkCreateResponse(response=repositories_response)
