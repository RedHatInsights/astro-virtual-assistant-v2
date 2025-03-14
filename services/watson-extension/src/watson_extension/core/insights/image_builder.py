import injector

from watson_extension.clients.insights.image_builder import ImageBuilderClient


class ImageBuilderCore:
    def __init__(self, image_builder_client: injector.Inject[ImageBuilderClient]):
        self.image_builder_client = image_builder_client

    async def enable_custom_repositories(self, version: str):
        return await self.image_builder_client.enable_custom_repositories(version)
