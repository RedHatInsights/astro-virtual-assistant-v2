from unittest.mock import MagicMock

import injector
import pytest
from quart.typing import TestClientProtocol

from watson_extension.clients.platform.rbac import (
    RBACClient,
    Roles,
)
from ..common import app_with_blueprint

from watson_extension.routes.platform.rbac import blueprint
from ... import async_value, get_test_template


@pytest.fixture
async def rbac_client() -> MagicMock:
    rbac_client = MagicMock(RBACClient)
    rbac_client.get_roles_for_tam = MagicMock(
        return_value=async_value(
            [
                Roles(
                    uuid="1001",
                    name="Automation Analytics Viewer",
                    display_name="Automation Analytics viewer",
                    description="Perform read operations on Automation Analytics resources.",
                    created="2021-06-14T13:53:00.990946Z",
                    modified="2024-09-19T20:07:20.563863Z",
                    policyCount=1562,
                    groups_in_count=3,
                    accessCount=1,
                    applications=["automation-analytics"],
                    system=True,
                    platform_default=False,
                    admin_default=False,
                    external_role_id=None,
                    external_tenant=None,
                ),
                Roles(
                    uuid="1002",
                    name="Foo Viewer",
                    display_name="Foo bariest",
                    description="Perform read operations on kung foo resources.",
                    created="2021-06-14T13:53:00.990946Z",
                    modified="2024-09-19T20:07:20.563863Z",
                    policyCount=1562,
                    groups_in_count=3,
                    accessCount=1,
                    applications=["foo-bar"],
                    system=True,
                    platform_default=False,
                    admin_default=False,
                    external_role_id=None,
                    external_tenant=None,
                ),
            ]
        )
    )
    return rbac_client


@pytest.fixture
async def test_client(rbac_client) -> TestClientProtocol:
    def injector_binder(binder: injector.Binder):
        binder.bind(RBACClient, rbac_client)

    return app_with_blueprint(blueprint, injector_binder).test_client()


@pytest.mark.asyncio
async def test_tam_request_network_error(test_client, rbac_client: MagicMock):
    rbac_client.get_roles_for_tam.side_effect = Exception("Mocked network error")

    with pytest.raises(Exception) as excinfo:
        await rbac_client.get_roles_for_tam()
    assert "Mocked network error" in str(excinfo.value)


async def test_tam_request_access(test_client, rbac_client) -> None:
    response = await test_client.post(
        "/rbac/tam-access",
        query_string={"account_id": "12345", "org_id": "foo", "duration": "3 days"},
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == get_test_template(
        "platform/rbac/submit_tam_access_request.txt"
    )
