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

async def test_tam_request_non_200(test_client, rbac_client: MagicMock):
    rbac_client.send_rbac_tam_request.return_value = MagicMock(
        ok=False,
        status=400,
        text=async_value("Bad Request"),
    )
    response = await test_client.post(
        "/rbac/tam-access",
        query_string={"account_id": "12345", "org_id": "foo", "duration": "3 days"},
    )

    assert response.status_code == 200 # ignores that
    data = await response.get_json()
    assert data["response"] == get_test_template(
        "platform/rbac/error_tam_access_request.txt"
    )

@pytest.mark.asyncio
async def test_tam_request_body(test_client, rbac_client: MagicMock):
    async def mock_send_rbac_tam_request(payload):
        assert payload.account_id == "12345"
        assert payload.org_id == "foo"
        assert payload.start_date == date.today().strftime("%m/%d/%Y")
        assert payload.end_date == (date.today() + timedelta(days=3)).strftime("%m/%d/%Y")
        assert payload.roles == ["Automation Analytics viewer", "Foo bariest"]
        return MagicMock(ok=True, status=200, text=async_value("Success"))

    rbac_client.send_rbac_tam_request.side_effect = mock_send_rbac_tam_request

    response = await test_client.post(
        "/rbac/tam-access",
        query_string={"account_id": "12345", "org_id": "foo", "duration": "3 days"},
    )

    assert response.status == "200 OK"

    data = await response.get_json()
    assert data["response"] == get_test_template(
        "platform/rbac/submit_tam_access_request.txt"
    )

@pytest.mark.parametrize(
    "duration, expected_end_date",
    [
        ("3 days", date.today() + timedelta(days=3)),
        ("1 week", date.today() + timedelta(weeks=1)),
        ("2 weeks", date.today() + timedelta(weeks=2)),
        ("invalid_duration", date.today()),
    ],
)
def test_get_start_end_date_from_duration(test_client, rbac_client: MagicMock, duration, expected_end_date):
    start_date, end_date = RBACCore(rbac_client=rbac_client).get_start_end_date_from_duration(duration)
    assert start_date == date.today().strftime("%m/%d/%Y")
    assert end_date == expected_end_date.strftime("%m/%d/%Y")
