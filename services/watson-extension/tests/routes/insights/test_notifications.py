from unittest.mock import MagicMock, AsyncMock

import injector
import pytest
from quart.typing import TestClientProtocol

from watson_extension.clients.insights.notifications import (
    NotificationsClient,
)
from ..common import app_with_blueprint

from watson_extension.routes.insights.notifications import blueprint


@pytest.fixture
async def notifications_client() -> MagicMock:
    return MagicMock(NotificationsClient)


@pytest.fixture
async def test_client(notifications_client) -> TestClientProtocol:
    def injector_binder(binder: injector.Binder):
        binder.bind(NotificationsClient, notifications_client)

    return app_with_blueprint(blueprint, injector_binder).test_client()


async def test_send_rbac_request_admin_email(test_client, notifications_client) -> None:
    notifications_client.send_notification = AsyncMock(return_value="")

    response = await test_client.post(
        "/notifications/send_rbac_request_admin_email?requested_url=example.com&user_message=plzzz approve",
    )
    assert response.status == "200 OK"
