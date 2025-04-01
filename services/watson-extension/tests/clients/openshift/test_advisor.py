import aiohttp
import pytest
from aioresponses import aioresponses

from ... import get_resource_contents
from watson_extension.clients import AdvisorOpenshiftURL
from common.identity import FixedUserIdentityProvider
from watson_extension.clients.openshift.advisor import (
    AdvisorClient,
    AdvisorClientHttp,
)
from common.platform_request import PlatformRequest


@pytest.fixture
async def aiohttp_mock():
    with aioresponses() as m:
        yield m


@pytest.fixture
async def session():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest.fixture
async def client(session) -> AdvisorClient:
    return AdvisorClientHttp(
        AdvisorOpenshiftURL(""), FixedUserIdentityProvider(), PlatformRequest(session)
    )


async def test_recommendations(client, aiohttp_mock) -> None:
    aiohttp_mock.get(
        "/api/insights-results-aggregator/v2/rule?impacting=true",
        status=200,
        body=get_resource_contents("requests/openshift/advisor/recommendations.json"),
    )
    recommendations = await client.get_recommendations()
    assert len(recommendations) == 3
    assert (
        recommendations[0].id
        == "ccx_rules_ocp.external.rules.cso_degraded_due_to_missing_privilege|CSO_DEGRADED_DUE_TO_MISSING_PRIVILIGES"
    )
    assert (
        recommendations[0].description
        == "The Cluster Storage Operator is degraded because the vCenter account misses the privilege of 'Inventory.Tagging.ObjectAttachable'"
    )
    assert recommendations[0].total_risk == 3

    assert (
        recommendations[1].id
        == "ccx_rules_ocp.external.rules.config_build_strategy_incorrect|CONFIG_BUILD_STRATEGY_INCORRECTLY"
    )
    assert (
        recommendations[1].description
        == "Configuring Build Strategy via admin or edit ClusterRoles is not recommended"
    )
    assert recommendations[1].total_risk == 3

    assert (
        recommendations[2].id
        == "ccx_rules_ocp.external.rules.okd_cluster_unsupported|OKD_CLUSTER_UNSUPPORTED"
    )
    assert (
        recommendations[2].description
        == "GSS does not provide enterprise-level support for an OKD cluster"
    )
    assert recommendations[2].total_risk == 2


async def test_workloads(client, aiohttp_mock) -> None:
    aiohttp_mock.get(
        "/api/insights-results-aggregator/v2/namespaces/dvo",
        status=200,
        body=get_resource_contents("requests/openshift/advisor/workloads.json"),
    )
    workloads = await client.get_workloads()
    assert len(workloads) == 3
    assert workloads[0].cluster_id == "207b5151-9c8b-4fcc-9f18-e97c4cf7b512"
    assert workloads[0].namespace_id == "626bdc9c-7f49-4410-ad68-41888489c0ef"
    assert (
        workloads[0].cluster_display_name == "CCX test cluster for DVO recommendations"
    )
    assert workloads[0].last_checked_at == "2025-03-31T13:18:25Z"

    assert workloads[1].cluster_id == "207b5151-9c8b-4fcc-9f18-e97c4cf7b512"
    assert workloads[1].namespace_id == "e94a4cc2-6b31-47d7-bdc5-eb14f7c5a4e5"
    assert (
        workloads[1].cluster_display_name == "CCX test cluster for DVO recommendations"
    )
    assert workloads[1].last_checked_at == "2025-03-31T13:18:25Z"

    assert workloads[2].cluster_id == "207b5151-9c8b-4fcc-9f18-e97c4cf7b512"
    assert workloads[2].namespace_id == "fe39d0d3-ea0b-4d37-bc3e-6358ed32ea18"
    assert (
        workloads[2].cluster_display_name == "CCX test cluster for DVO recommendations"
    )
    assert workloads[2].last_checked_at is None


async def test_clusters(client, aiohttp_mock) -> None:
    aiohttp_mock.get(
        "/api/insights-results-aggregator/v2/clusters",
        status=200,
        body=get_resource_contents("requests/openshift/advisor/clusters.json"),
    )
    clusters = await client.get_clusters()
    assert len(clusters) == 3
    assert clusters[0].id == "f0cc23f7-5dfa-440a-88f1-5a43e75b74d1"
    assert clusters[0].name == "Test disable recommendation"
    assert clusters[0].last_checked_at == "2025-03-31T13:25:59Z"

    assert clusters[1].id == "ee7d2bf4-8933-4a3a-8634-3328fe806e08"
    assert clusters[1].name == "No Issues Cluster"
    assert clusters[1].last_checked_at == "2025-03-31T13:25:56Z"

    assert clusters[2].id == "98ed1b12-08f2-11f0-9801-525400fdfea5"
    assert clusters[2].name == "iqe-ocp-vulnerability-stage-test-mar24"
    assert clusters[2].last_checked_at is None
