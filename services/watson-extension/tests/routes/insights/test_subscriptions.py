from unittest.mock import MagicMock

import injector
import pytest
from quart.typing import TestClientProtocol

from watson_extension.clients.insights.rhsm import SubscriptionInfo, RhsmClient
from ..common import app_with_blueprint

from watson_extension.routes.insights.rhsm import blueprint
from ... import async_value


@pytest.fixture
async def rhsm_client() -> MagicMock:
    return MagicMock(RhsmClient)


@pytest.fixture
async def test_client(rhsm_client) -> TestClientProtocol:
    def injector_binder(binder: injector.Binder):
        binder.bind(RhsmClient, rhsm_client)

    return app_with_blueprint(blueprint, injector_binder).test_client()


async def test_check_subscriptions_all(test_client, rhsm_client, snapshot) -> None:
    rhsm_client.check_subscriptions = MagicMock(
        return_value=async_value(
            [
                SubscriptionInfo(
                    number="200",
                    category="active",
                ),
                SubscriptionInfo(
                    number="25",
                    category="expiring",
                ),
                SubscriptionInfo(
                    number="30",
                    category="expired",
                ),
            ]
        )
    )

    response = await test_client.get(
        "/rhsm/check_subscriptions",
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == snapshot


async def test_check_subscriptions_one(test_client, rhsm_client, snapshot) -> None:
    rhsm_client.check_subscriptions = MagicMock(
        return_value=async_value(
            [
                SubscriptionInfo(
                    number="10",
                    category="expiring",
                ),
            ]
        )
    )

    response = await test_client.get(
        "/rhsm/check_subscriptions?category=expiringSoon",
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == snapshot


async def test_check_subscriptions_none(test_client, rhsm_client, snapshot) -> None:
    rhsm_client.check_subscriptions = MagicMock(return_value=async_value([]))

    response = await test_client.get(
        "/rhsm/check_subscriptions",
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == snapshot
