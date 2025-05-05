from unittest.mock import MagicMock, AsyncMock

import injector
import pytest
from quart.typing import TestClientProtocol

from watson_extension.clients.general.redhat_status import (
    RedhatStatusClient,
)
from ..common import app_with_blueprint

from watson_extension.routes.general.redhat_status import blueprint
from ... import async_value


@pytest.fixture
async def redhat_status_client() -> MagicMock:
    return MagicMock(RedhatStatusClient)


@pytest.fixture
async def test_client(redhat_status_client) -> TestClientProtocol:
    def injector_binder(binder: injector.Binder):
        binder.bind(RedhatStatusClient, redhat_status_client)

    return app_with_blueprint(blueprint, injector_binder).test_client()


async def test_check_services_offline_incident_exists(
    test_client, redhat_status_client
) -> None:
    check_services_offline_response = AsyncMock()
    check_services_offline_response.ok = True
    check_services_offline_response.json = MagicMock(
        return_value=async_value(
            {
                "incidents": [
                    {
                        "id": "oiia-oiia",
                        "name": "OIIA OIIA CAT",
                        "status": "investigating",
                    }
                ]
            }
        )
    )

    redhat_status_client.check_services_offline = MagicMock(
        return_value=async_value(check_services_offline_response)
    )

    response = await test_client.get("/redhat_status/check_services_offline")
    assert response.status == "200 OK"

    data = await response.get_json()
    assert data["count"] == "1"
    assert data["response_type"] == "incident_exists"
    assert data["incidents"][0]["name"] == "OIIA OIIA CAT"
    assert data["incidents"][0]["status"] == "investigating"


async def test_check_services_offline_no_incidents(
    test_client, redhat_status_client
) -> None:
    check_services_offline_response = AsyncMock()
    check_services_offline_response.ok = True
    check_services_offline_response.json = MagicMock(
        return_value=async_value({"incidents": []})
    )

    redhat_status_client.check_services_offline = MagicMock(
        return_value=async_value(check_services_offline_response)
    )

    response = await test_client.get("/redhat_status/check_services_offline")
    assert response.status == "200 OK"

    data = await response.get_json()
    assert data["response_type"] == "no_incidents"
    assert data["count"] == "0"
    assert data["incidents"] == []


async def test_check_services_offline_error(test_client, redhat_status_client) -> None:
    check_services_offline_response = AsyncMock()
    check_services_offline_response.ok = False
    check_services_offline_response.json = MagicMock(return_value=async_value({}))

    redhat_status_client.check_services_offline = MagicMock(
        return_value=async_value(check_services_offline_response)
    )

    response = await test_client.get("/redhat_status/check_services_offline")
    assert response.status == "200 OK"

    data = await response.get_json()
    assert data["response_type"] == "error"
    assert data["count"] == "0"
    assert data["incidents"] == []
