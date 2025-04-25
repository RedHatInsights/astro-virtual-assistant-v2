import enum
from typing import Optional, List, Tuple

import injector

from watson_extension.clients.platform import IntegrationInfo
from watson_extension.clients.platform.integrations import IntegrationsClient
from watson_extension.clients.platform.sources import SourcesClient


MAX_NUMBER_OF_INTEGRATIONS = 5


class IntegrationType(enum.Enum):
    REDHAT = "red_hat"
    NOTIFICATIONS = "notifications"


class IntegrationsCore:
    def __init__(
        self,
        integrations_client: injector.Inject[IntegrationsClient],
        sources_client: injector.Inject[SourcesClient],
    ):
        self.integrations_client = integrations_client
        self.sources_client = sources_client

    async def redhat_integrations_validate_name(
        self,
        integrations_setup_name: str,
    ) -> bool:
        return await self.sources_client.is_source_name_valid(integrations_setup_name)

    async def redhat_integrations_setup(
        self, integrations_setup_name: str, redhat_cluster_identifier: str
    ) -> bool:
        return await self.sources_client.bulk_create(
            integrations_setup_name, redhat_cluster_identifier
        )

    async def communications_integrations_setup(
        self,
        setup_name: str,
        setup_url: str,
        setup_secret: str,
        setup_use_secret: bool,
        setup_type: Optional[str] = None,
    ) -> bool:
        return await self.integrations_client.create_endpoint(
            setup_name=setup_name,
            setup_url=setup_url,
            secret_token=setup_secret if setup_use_secret is True else None,
            setup_type="camel",
            setup_sub_type=setup_type,
        )

    async def reporting_integrations_setup(
        self,
        setup_name: str,
        setup_url: str,
        setup_secret: str,
        setup_use_secret: bool,
        setup_type: Optional[str] = None,
    ) -> bool:
        return await self.integrations_client.create_endpoint(
            setup_name=setup_name,
            setup_url=setup_url,
            secret_token=setup_secret if setup_use_secret is True else None,
            setup_type=setup_type,
            setup_sub_type=setup_type,
        )

    async def webhook_integrations_setup(
        self,
        setup_name: str,
        setup_url: str,
        setup_secret: str,
        setup_use_secret: bool,
    ) -> bool:
        return await self.integrations_client.create_endpoint(
            setup_name=setup_name,
            setup_url=setup_url,
            secret_token=setup_secret if setup_use_secret is True else None,
            setup_type="webhook",
        )

    async def fetch_integrations(
        self,
        integration_search: Optional[str] = None,
        integration_enabled: Optional[bool] = None,
    ) -> Tuple[bool, Optional[List[IntegrationInfo]]]:
        has_errors = False

        (
            response_ok,
            notification_api_integrations,
        ) = await self.integrations_client.fetch_integrations(
            search=integration_search,
            enabled=integration_enabled,
            max_integration_num=MAX_NUMBER_OF_INTEGRATIONS,
        )

        if not response_ok:
            has_errors = True

        response_ok, sources_api_integrations = await self.sources_client.get_sources(
            search=integration_search,
            enabled=integration_enabled,
            max_integration_num=MAX_NUMBER_OF_INTEGRATIONS,
        )

        if not response_ok:
            has_errors = True

        integrations = [*notification_api_integrations, *sources_api_integrations]

        return has_errors, integrations[:5]

    async def integration_enable(
        self,
        integration_type: IntegrationType,
        integration_id: str,
    ) -> bool:
        response = None

        if integration_type.value == IntegrationType.REDHAT:
            response = await self.sources_client.sources_unpause_integration(
                integration_id
            )
        elif integration_type.value == IntegrationType.NOTIFICATIONS:
            response = await self.integrations_client.integration_resume(integration_id)

        if response is not None and response.ok:
            return True

        return False

    async def integration_disable(
        self,
        integration_type: IntegrationType,
        integration_id: str,
    ) -> bool:
        response = None

        if integration_type.value == IntegrationType.REDHAT:
            response = await self.sources_client.sources_pause_integration(
                integration_id
            )
        elif integration_type.value == IntegrationType.NOTIFICATIONS:
            response = await self.integrations_client.integration_pause(integration_id)

        if response is not None and response.ok:
            return True

        return False

    async def integration_delete(
        self,
        integration_type: IntegrationType,
        integration_id: str,
    ) -> bool:
        response = None

        if integration_type.value == IntegrationType.REDHAT:
            response = await self.sources_client.sources_delete_integration(
                integration_id
            )
        elif integration_type.value == IntegrationType.NOTIFICATIONS:
            response = await self.integrations_client.delete_integration(integration_id)

        if response is not None and response.ok:
            return True

        return False

    async def integration_update_name(
        self,
        integration_type: IntegrationType,
        integration_id: str,
        new_integration_name: str,
    ) -> bool:
        response = None

        if integration_type.value == IntegrationType.REDHAT:
            response = await self.sources_client.sources_update_integration(
                integration_id=integration_id,
                integration_data={"name": new_integration_name},
            )
        elif integration_type.value == IntegrationType.NOTIFICATIONS:
            response = self.integrations_client.retrieve_notification_endpoint(
                integration_id
            )

            if response.ok:
                integration_data = await response.json()
                integration_data["name"] = new_integration_name

                response = await self.integrations_client.update_integration(
                    integration_id=integration_id, integration_data=integration_data
                )

        if response is not None and response.ok:
            return True

        return False

    async def integration_update_url(
        self,
        integration_type: IntegrationType,
        integration_id: str,
        new_integration_url: str,
    ) -> bool:
        response = None

        if integration_type.value == IntegrationType.NOTIFICATIONS:
            response = self.integrations_client.retrieve_notification_endpoint(
                integration_id
            )

            if response.ok:
                integration_data = await response.json()
                integration_data["properties"]["url"] = new_integration_url

                response = await self.integrations_client.update_integration(
                    integration_id=integration_id, integration_data=integration_data
                )

        if response is not None and response.ok:
            return True

        return False

    async def integration_update_secret(
        self,
        integration_type: IntegrationType,
        integration_id: str,
        new_integration_secret: str,
    ) -> bool:
        response = None

        if integration_type.value == IntegrationType.NOTIFICATIONS:
            response = self.integrations_client.retrieve_notification_endpoint(
                integration_id
            )

            if response.ok:
                integration_data = await response.json()
                integration_data["properties"]["secret_token"] = new_integration_secret

                response = await self.integrations_client.update_integration(
                    integration_id=integration_id, integration_data=integration_data
                )

        if response is not None and response.ok:
            return True

        return False
