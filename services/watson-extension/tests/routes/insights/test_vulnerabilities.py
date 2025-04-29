from unittest.mock import MagicMock

import injector
import pytest
from quart.typing import TestClientProtocol

from watson_extension.clients.insights.vulnerability import CVEInfo, VulnerabilityClient
from ..common import app_with_blueprint

from watson_extension.routes.insights.vulnerability import blueprint
from ... import async_value


@pytest.fixture
async def vulnerability_client() -> MagicMock:
    return MagicMock(VulnerabilityClient)


@pytest.fixture
async def test_client(vulnerability_client) -> TestClientProtocol:
    def injector_binder(binder: injector.Binder):
        binder.bind(VulnerabilityClient, vulnerability_client)

    return app_with_blueprint(blueprint, injector_binder).test_client()


async def test_cves(test_client, vulnerability_client, snapshot) -> None:
    vulnerability_client.find_cves = MagicMock(
        return_value=async_value(
            [
                CVEInfo(
                    id="CVE-1337-7331",
                    systems_affected="1234",
                    impact="Critical",
                    link="/insights/vulnerability/cves/CVE-1337-7331",
                )
            ]
        )
    )

    response = await test_client.get(
        "/vulnerability/cves",
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == snapshot


async def test_cves_none(test_client, vulnerability_client, snapshot) -> None:
    vulnerability_client.find_cves = MagicMock(return_value=async_value([]))

    response = await test_client.get(
        "/vulnerability/cves",
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == snapshot
