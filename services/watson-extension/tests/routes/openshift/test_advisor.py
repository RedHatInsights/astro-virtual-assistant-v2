from unittest.mock import MagicMock

import injector
import pytest
from quart.typing import TestClientProtocol

from watson_extension.clients.openshift.advisor import (
    AdvisorClient,
    Recommendation,
    Workload,
    Cluster,
)
from ..common import app_with_blueprint

from watson_extension.routes.openshift.advisor import blueprint
from ... import async_value, get_test_template


@pytest.fixture
async def advisor_client() -> MagicMock:
    return MagicMock(AdvisorClient)


@pytest.fixture
async def test_client(advisor_client) -> TestClientProtocol:
    def injector_binder(binder: injector.Binder):
        binder.bind(AdvisorClient, advisor_client)

    return app_with_blueprint(blueprint, injector_binder).test_client()


async def test_recommendations(test_client, advisor_client) -> None:
    advisor_client.get_recommendations = MagicMock(
        return_value=async_value(
            [
                Recommendation(
                    description="recommendation 1", total_risk=13, id="my-id"
                ),
                Recommendation(
                    description="recommendation 2", total_risk=5, id="my-id-2"
                ),
            ]
        )
    )

    response = await test_client.get(
        "/advisor/recommendations", query_string={"category": "recommendation"}
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == get_test_template(
        "openshift/advisor/recommendations.txt"
    )


async def test_workloads(test_client, advisor_client) -> None:
    advisor_client.get_workloads = MagicMock(
        return_value=async_value(
            [
                Workload(
                    cluster_id="cluster-001",
                    cluster_display_name="My cluster1",
                    namespace_id="my-namespace",
                    last_checked_at="2025-03-31T13:51:18+00:00",
                ),
                Workload(
                    cluster_id="cluster-001",
                    cluster_display_name="My cluster5",
                    namespace_id="somewhere",
                    last_checked_at="2025-03-30T13:51:18+00:00",
                ),
                Workload(
                    cluster_id="cluster-003",
                    cluster_display_name="My cluster10",
                    namespace_id="etc",
                    last_checked_at="2025-03-29T13:51:18+00:00",
                ),
            ]
        )
    )

    response = await test_client.get(
        "/advisor/recommendations", query_string={"category": "workload"}
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == get_test_template("openshift/advisor/workload.txt")


async def test_clusters(test_client, advisor_client) -> None:
    advisor_client.get_clusters = MagicMock(
        return_value=async_value(
            [
                Cluster(
                    id="007", name="Bond", last_checked_at="2025-03-31T13:51:18+00:00"
                ),
                Cluster(
                    id="one", name="Johnny", last_checked_at="2025-03-30T13:51:18+00:00"
                ),
            ]
        )
    )

    response = await test_client.get(
        "/advisor/recommendations", query_string={"category": "cluster"}
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == get_test_template("openshift/advisor/cluster.txt")


async def test_recommendations_none(test_client, advisor_client) -> None:
    advisor_client.get_recommendations = MagicMock(return_value=async_value([]))

    response = await test_client.get(
        "/advisor/recommendations", query_string={"category": "recommendation"}
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == get_test_template(
        "openshift/advisor/no-recommendations.txt"
    )
