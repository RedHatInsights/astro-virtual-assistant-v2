from unittest.mock import MagicMock, AsyncMock

import injector
import pytest
from quart.typing import TestClientProtocol

from watson_extension.clients.platform.notifications import PlatformNotificationsClient
from ..common import app_with_blueprint

from watson_extension.routes.platform.notifications import blueprint
from ... import async_value


@pytest.fixture
async def platform_notifications_client() -> MagicMock:
    return MagicMock(PlatformNotificationsClient)


@pytest.fixture
async def test_client(platform_notifications_client) -> TestClientProtocol:
    def injector_binder(binder: injector.Binder):
        binder.bind(PlatformNotificationsClient, platform_notifications_client)

    return app_with_blueprint(blueprint, injector_binder).test_client()


async def test_notifications_event_options(
    test_client, platform_notifications_client
) -> None:
    platform_notifications_client.get_available_bundles = MagicMock(
        return_value=async_value(
            [
                {
                    "id": "8a1d329e-7865-4751-b468-e764fe499887",
                    "name": "rhel",
                    "displayName": "Red Hat Enterprise Linux",
                    "children": None,
                },
            ]
        )
    )

    platform_notifications_client.get_available_events_by_bundle = MagicMock(
        return_value=async_value(
            {
                "data": [
                    {
                        "id": "5eaec47c-2eb2-4179-88cd-2e6757955283",
                        "name": "deactivated-recommendation",
                        "display_name": "Deactivated recommendation",
                        "description": "",
                        "application_id": "c104e056-a77a-4512-a1e8-f00bcba4d8a9",
                        "application": {
                            "created": "2024-01-08T03:00:21.554545",
                            "id": "c104e056-a77a-4512-a1e8-f00bcba4d8a9",
                            "name": "advisor",
                            "display_name": "Advisor",
                            "bundle_id": "8a1d329e-7865-4751-b468-e764fe499887",
                        },
                        "visible": True,
                        "subscribed_by_default": False,
                        "subscription_locked": False,
                        "restrict_to_recipients_integrations": False,
                    }
                ]
            }
        )
    )

    response = await test_client.get(
        "/notifications/notifications_event/options",
        query_string={"bundle_name": "rhel"},
    )
    assert response.status == "200 OK"
    data = await response.get_json()

    assert data["options"] == [
        {
            "application_display_name": "Advisor",
            "application_id": "c104e056-a77a-4512-a1e8-f00bcba4d8a9",
            "application_name": "advisor",
            "bundle_id": "8a1d329e-7865-4751-b468-e764fe499887",
            "display_name": "Deactivated recommendation",
            "id": "5eaec47c-2eb2-4179-88cd-2e6757955283",
            "name": "deactivated-recommendation",
        }
    ]


async def test_remove_behavior_group_success(
    test_client, platform_notifications_client
) -> None:
    platform_notifications_client.get_behavior_groups = MagicMock(
        return_value=async_value([{"test": "yes"}])
    )

    mute_event_response = AsyncMock()
    mute_event_response.status = 200

    platform_notifications_client.mute_event = MagicMock(
        return_value=async_value(mute_event_response)
    )

    query_params = {
        "bundle_id": "8a1d329e-7865-4751-b468-e764fe499887",
        "event_id": "f2130a90-a0a6-41a8-97d2-84223ffe9900",
        "event_application_display_name": "Advisor",
    }
    response = await test_client.get(
        "/notifications/remove_behavior_group", query_string=query_params
    )
    assert response.status == "200 OK"
    data = await response.get_json()

    assert data["response"] == "I have muted notifications for the Advisor event."


async def test_remove_behavior_group_error(
    test_client, platform_notifications_client
) -> None:
    platform_notifications_client.get_behavior_groups = MagicMock(
        return_value=async_value([{"test": "yes"}])
    )

    mute_event_response = AsyncMock()
    mute_event_response.ok = False

    platform_notifications_client.mute_event = MagicMock(
        return_value=async_value(mute_event_response)
    )

    query_params = {
        "bundle_id": "8a1d329e-7865-4751-b468-e764fe499887",
        "event_id": "f2130a90-a0a6-41a8-97d2-84223ffe9900",
        "event_application_display_name": "Advisor",
    }
    response = await test_client.get(
        "/notifications/remove_behavior_group", query_string=query_params
    )
    assert response.status == "200 OK"
    data = await response.get_json()

    assert (
        data["response"] == "I was unable to mute this event. Please try again later."
    )


async def test_remove_behavior_group_no_behavior_group(
    test_client, platform_notifications_client
) -> None:
    platform_notifications_client.get_behavior_groups = MagicMock(
        return_value=async_value([])
    )

    mute_event_response = AsyncMock()
    mute_event_response.ok = False

    platform_notifications_client.mute_event = MagicMock(
        return_value=async_value(mute_event_response)
    )

    query_params = {
        "bundle_id": "8a1d329e-7865-4751-b468-e764fe499887",
        "event_id": "f2130a90-a0a6-41a8-97d2-84223ffe9900",
        "event_application_display_name": "Advisor",
    }
    response = await test_client.get(
        "/notifications/remove_behavior_group", query_string=query_params
    )
    assert response.status == "200 OK"
    data = await response.get_json()

    assert (
        data["response"]
        == "You don't have any behavior groups attached to the Advisor event yet."
    )
