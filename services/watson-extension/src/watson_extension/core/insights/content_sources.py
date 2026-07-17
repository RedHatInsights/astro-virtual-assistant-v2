import injector

from watson_extension.clients.insights.content_sources import ContentSourcesClient


class ContentSourcesCore:
    def __init__(self, content_sources_client: injector.Inject[ContentSourcesClient]):
        self.content_sources_client = content_sources_client

    async def enable_custom_repositories(self, version: str):
        popular_repositories = (
            await self.content_sources_client.get_popular_repositories()
        )

        repository = None
        for repo in popular_repositories.data:
            if repo["suggested_name"] and repo["suggested_name"].startswith(version):
                repository = repo
                break

        formatted_repository_info = [
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

        return await self.content_sources_client.repositories_bulk_create(
            formatted_repository_info
        )
