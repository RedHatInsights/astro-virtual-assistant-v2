import abc
from dataclasses import dataclass
from typing import Optional

import injector

from watson_extension.clients import ContentSourcesURL
from watson_extension.clients.identity import AbstractUserIdentityProvider
from watson_extension.clients.platform_request import AbstractPlatformRequest


@dataclass
class EnableCustomRepositoriesResponse:
    response: Optional[str] = None


class ImageBuilderClient(abc.ABC):
    @abc.abstractmethod
    async def enable_custom_repositories(
        self, version: str
    ) -> EnableCustomRepositoriesResponse: ...


class ImageBuilderClientHttp(ImageBuilderClient):
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

    async def enable_custom_repositories(
        self,
        version: str,
    ) -> EnableCustomRepositoriesResponse:
        request = "/api/content-sources/v1/popular_repositories/?offset=0&limit=20"
        response = await self.platform_request.get(
            self.content_sources_url,
            request,
            user_identity=await self.user_identity_provider.get_user_identity(),
        )
        response.raise_for_status()

        content = await response.json()

        repository = None
        for repo in content["data"]:
            if repo["suggested_name"] and repo["suggested_name"].startswith(version):
                repository = repo
                break

        headers = {"Content-Type": "application/json"}
        formatted = [
            {
                "name": repository["suggested_name"],
                "distribution_arch": repository["distribution_arch"],
                "distribution_versions": repository["distribution_versions"],
                "gpg_key": repository["gpg_key"],
                "metadata_verification": repository["metadata_verification"],
                "snapshot": False,
                "url": repository["url"],
            }
        ]

        request = "/api/content-sources/v1.0/repositories/bulk_create/"
        response = await self.platform_request.post(
            self.content_sources_url,
            request,
            user_identity=await self.user_identity_provider.get_user_identity(),
            json=formatted,
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

        return EnableCustomRepositoriesResponse(response=repositories_response)
