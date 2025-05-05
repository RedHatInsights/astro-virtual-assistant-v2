from datetime import date, timedelta
from unittest.mock import MagicMock

import injector
import pytest
from quart.typing import TestClientProtocol

from watson_extension.clients.platform.rbac import (
    RBACClient,
    Roles,
)
from watson_extension.core.platform.rbac import RBACCore

from ..common import app_with_blueprint
from watson_extension.routes.platform.rbac import blueprint
from ... import async_value


@pytest.fixture
async def rbac_client() -> MagicMock:
    rbac_client = MagicMock(RBACClient)
    return rbac_client


@pytest.fixture
async def test_client(rbac_client) -> TestClientProtocol:
    def injector_binder(binder: injector.Binder):
        binder.bind(RBACClient, rbac_client)

    return app_with_blueprint(blueprint, injector_binder).test_client()


async def test_rbac_org_id(test_client, rbac_client, snapshot) -> None:
    response = await test_client.get(
        "/rbac/org-id",
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == snapshot
