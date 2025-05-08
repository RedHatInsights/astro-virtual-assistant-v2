from unittest.mock import MagicMock, AsyncMock

import injector
import pytest
from quart.typing import TestClientProtocol

from watson_extension.clients.platform import IntegrationInfo
from watson_extension.clients.platform.integrations import IntegrationsClient
from watson_extension.clients.platform.sources import SourcesClient
from ..common import app_with_blueprint

from watson_extension.routes.platform.integrations import blueprint
from ... import async_value, get_test_template


@pytest.fixture
async def integrations_client() -> MagicMock:
    return MagicMock(IntegrationsClient)


@pytest.fixture
async def sources_client() -> MagicMock:
    return MagicMock(SourcesClient)


@pytest.fixture
async def test_client(integrations_client, sources_client) -> TestClientProtocol:
    def injector_binder(binder: injector.Binder):
        binder.bind(IntegrationsClient, integrations_client)
        binder.bind(SourcesClient, sources_client)

    return app_with_blueprint(blueprint, injector_binder).test_client()


async def test_fetch_integrations(
    test_client, integrations_client, sources_client
) -> None:
    integrations_client.fetch_integrations = MagicMock(
        return_value=async_value(
            (
                [
                    True,
                    [
                        IntegrationInfo(
                            enabled=True,
                            group="webhook",
                            id="1234",
                            name="test integration",
                            type="notifications",
                        )
                    ],
                ]
            )
        )
    )
    sources_client.get_sources = MagicMock(
        return_value=async_value(
            (
                [
                    True,
                    [
                        IntegrationInfo(
                            enabled=True,
                            group="red_hat",
                            id="5678",
                            name="test sources",
                            type="red_hat",
                        )
                    ],
                ]
            )
        )
    )

    response = await test_client.get(
        "/integrations/options?integration_search_query=test&integration_enabled=true"
    )

    assert response.status == "200 OK"

    integrations_client.fetch_integrations.assert_called_once_with(
        search="test", enabled=True, max_integration_num=5
    )

    data = await response.get_json()

    assert data == {
        "has_errors": False,
        "integrations": [
            {
                "enabled": True,
                "group": "webhook",
                "id": "1234",
                "name": "test integration",
                "type": "notifications",
            },
            {
                "enabled": True,
                "group": "red_hat",
                "id": "5678",
                "name": "test sources",
                "type": "red_hat",
            },
        ],
    }


async def test_fetch_integrations_error(
    test_client, integrations_client, sources_client
) -> None:
    integrations_client.fetch_integrations = MagicMock(
        return_value=async_value(
            (
                [
                    True,
                    [
                        IntegrationInfo(
                            enabled=True,
                            group="webhook",
                            id="1234",
                            name="test integration",
                            type="notifications",
                        )
                    ],
                ]
            )
        )
    )

    sources_client.get_sources = MagicMock(return_value=async_value(([False, []])))

    response = await test_client.get("/integrations/options")

    assert response.status == "200 OK"

    data = await response.get_json()
    assert data == {
        "has_errors": True,
        "integrations": [
            {
                "enabled": True,
                "group": "webhook",
                "id": "1234",
                "name": "test integration",
                "type": "notifications",
            }
        ],
    }


async def test_integration_actions(test_client, integrations_client) -> None:
    integration_pause_response = AsyncMock()
    integration_pause_response.ok = True

    integrations_client.integration_pause = MagicMock(
        return_value=async_value(integration_pause_response)
    )

    response = await test_client.post(
        "/integrations/actions?action_type=pause&integration_type=notifications&integration_id=1234"
    )

    assert response.status == "200 OK"

    integrations_client.integration_pause.assert_called_once_with("1234")

    data = await response.get_json()

    assert (
        data["response"]
        == "Got it. Your integration was successfully disabled. You can confirm that your desired changes have been made on the [Integrations page](/settings/integrations) if you'd like."
    )


async def test_integration_actions_sources(test_client, sources_client) -> None:
    integration_delete_response = AsyncMock()
    integration_delete_response.ok = True

    sources_client.sources_delete_integration = MagicMock(
        return_value=async_value(integration_delete_response)
    )

    response = await test_client.post(
        "/integrations/actions?action_type=delete&integration_type=red_hat&integration_id=5678"
    )

    assert response.status == "200 OK"

    sources_client.sources_delete_integration.assert_called_once_with("5678")

    data = await response.get_json()

    assert data["response"] == "Your integration was successfully deleted."


async def test_integration_actions_error(test_client, integrations_client) -> None:
    integration_pause_response = AsyncMock()
    integration_pause_response.ok = False

    integrations_client.integration_pause = MagicMock(
        return_value=async_value(integration_pause_response)
    )

    response = await test_client.post(
        "/integrations/actions?action_type=pause&integration_type=notifications&integration_id=1234"
    )

    assert response.status == "200 OK"

    integrations_client.integration_pause.assert_called_once_with("1234")

    data = await response.get_json()

    assert data["response"] == get_test_template(
        "platform/integrations/integration_edit_error.txt"
    )


async def test_integration_update(test_client, integrations_client) -> None:
    integration_retrieve_endpoint = AsyncMock()
    integration_retrieve_endpoint.ok = True
    integration_retrieve_endpoint.json = MagicMock(return_value=async_value({}))
    integrations_client.retrieve_notification_endpoint = MagicMock(
        return_value=async_value(integration_retrieve_endpoint)
    )

    integration_update_response = AsyncMock()
    integration_update_response.ok = True
    integrations_client.update_integration = MagicMock(
        return_value=async_value(integration_update_response)
    )

    response = await test_client.post(
        "/integrations/update?update_type=name&integration_type=notifications&integration_id=1234&new_value=new_test_name"
    )

    assert response.status == "200 OK"

    integrations_client.retrieve_notification_endpoint.assert_called_once_with("1234")
    integrations_client.update_integration.assert_called_once_with(
        integration_id="1234", integration_data={"name": "new_test_name"}
    )

    data = await response.get_json()

    assert (
        data["response"]
        == "The name of your integration was successfully updated to new_test_name."
    )


async def test_integration_update_error(test_client, sources_client) -> None:
    integration_update_response = AsyncMock()
    integration_update_response.ok = False
    sources_client.sources_update_integration = MagicMock(
        return_value=async_value(integration_update_response)
    )

    response = await test_client.post(
        "/integrations/update?update_type=name&integration_type=red_hat&integration_id=5678&new_value=new_redhat_val"
    )

    assert response.status == "200 OK"

    sources_client.sources_update_integration.assert_called_once_with(
        integration_id="5678", integration_data={"name": "new_redhat_val"}
    )

    data = await response.get_json()

    assert data["response"] == get_test_template(
        "platform/integrations/integration_edit_error.txt"
    )


async def test_integration_create(test_client, integrations_client) -> None:
    integrations_client.create_endpoint = MagicMock(return_value=async_value(True))

    response = await test_client.post(
        "/integrations/setup?integration_type=reporting&setup_name=test&setup_url=https://example.com&setup_secret=shhh&setup_use_secret=true&setup_type=ansible"
    )

    assert response.status == "200 OK"

    integrations_client.create_endpoint.assert_called_once_with(
        setup_name="test",
        setup_url="https://example.com",
        secret_token="shhh",
        setup_type="ansible",
        setup_sub_type=None,
    )

    data = await response.get_json()

    assert (
        data["response"]
        == "Your ansible integration was successfully created. You can view your new integration on the Reporting & Automation tab."
    )


async def test_integration_create_invalid_setup_type(
    test_client, integrations_client
) -> None:
    integrations_client.create_endpoint = MagicMock(return_value=async_value(True))

    response = await test_client.post(
        "/integrations/setup?integration_type=communications&setup_name=test&setup_url=https://example.com&setup_secret=shhh&setup_use_secret=true&setup_type=idk"
    )

    assert response.status == "200 OK"

    data = await response.get_json()

    assert data["response"] == get_test_template(
        "platform/integrations/integration_create_error.txt"
    )


async def test_integration_redhat_name_valid(test_client, sources_client) -> None:
    sources_client.is_source_name_valid = MagicMock(return_value=async_value(True))

    response = await test_client.get(
        "/integrations/redhat/check_name_valid?integrations_setup_name=test name"
    )

    assert response.status == "200 OK"

    sources_client.is_source_name_valid.assert_called_once_with("test name")

    data = await response.get_json()

    assert data["integration_name_valid"]


async def test_integration_redhat_setup(test_client, sources_client) -> None:
    sources_client.bulk_create = MagicMock(return_value=async_value(True))

    response = await test_client.post(
        "/integrations/redhat/setup?integrations_setup_name=test&redhat_cluster_identifier=abcdef"
    )

    assert response.status == "200 OK"

    sources_client.bulk_create.assert_called_once_with("test", "abcdef")

    data = await response.get_json()

    assert (
        data["response"]
        == "Your Red Hat OpenShift Container Platform integration was successfully created. You can view your new integration on the Red Hat tab."
    )


async def test_integration_redhat_setup_error(test_client, sources_client) -> None:
    sources_client.bulk_create = MagicMock(return_value=async_value(False))

    response = await test_client.post(
        "/integrations/redhat/setup?integrations_setup_name=test&redhat_cluster_identifier=abcdef"
    )

    assert response.status == "200 OK"

    sources_client.bulk_create.assert_called_once_with("test", "abcdef")

    data = await response.get_json()

    assert data["response"] == get_test_template(
        "platform/integrations/integration_create_error.txt"
    )
