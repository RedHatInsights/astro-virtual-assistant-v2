import abc
import injector
from dataclasses import dataclass
from typing import List, Optional

from common.identity import AbstractUserIdentityProvider
from common.platform_request import AbstractPlatformRequest
from watson_extension.clients import AdvisorOpenshiftURL


@dataclass
class Cluster:
    id: str
    name: str
    last_checked_at: Optional[str] = None


@dataclass
class Workload:
    cluster_display_name: str
    cluster_id: str
    namespace_id: str
    last_checked_at: Optional[str] = None


@dataclass
class Recommendation:
    id: str
    description: str
    total_risk: int


class AdvisorClient(abc.ABC):
    @abc.abstractmethod
    async def get_clusters(self) -> List[Cluster]: ...

    @abc.abstractmethod
    async def get_workloads(self) -> List[Workload]: ...

    @abc.abstractmethod
    async def get_recommendations(self) -> List[Recommendation]: ...


class AdvisorClientHttp(AdvisorClient):
    def __init__(
        self,
        advisor_url: injector.Inject[AdvisorOpenshiftURL],
        user_identity_provider: injector.Inject[AbstractUserIdentityProvider],
        platform_request: injector.Inject[AbstractPlatformRequest],
    ):
        super().__init__()
        self.advisor_url = advisor_url
        self.user_identity_provider = user_identity_provider
        self.platform_request = platform_request

    async def get_clusters(self) -> List[Cluster]:
        response = await self.platform_request.get(
            self.advisor_url,
            "/api/insights-results-aggregator/v2/clusters",
            user_identity=await self.user_identity_provider.get_user_identity(),
        )
        response.raise_for_status()

        content = await response.json()

        clusters = [
            Cluster(
                id=c["cluster_id"],
                name=c["cluster_name"],
                last_checked_at=c["last_checked_at"]
                if "last_checked_at" in c
                else None,
            )
            for c in content["data"]
        ]

        clusters.sort(
            key=lambda c: [c.last_checked_at] if c.last_checked_at is not None else [],
            reverse=True,
        )

        return clusters[:3]

    async def get_workloads(self) -> List[Workload]:
        response = await self.platform_request.get(
            self.advisor_url,
            "/api/insights-results-aggregator/v2/namespaces/dvo",
            user_identity=await self.user_identity_provider.get_user_identity(),
        )
        response.raise_for_status()

        content = await response.json()
        if content["status"] != "ok":
            raise RuntimeError(
                f"Received invalid status from openshift_advisor/workloads: {content['status']}"
            )

        workloads = [
            Workload(
                cluster_id=w["cluster"]["uuid"],
                cluster_display_name=w["cluster"]["display_name"],
                namespace_id=w["namespace"]["uuid"],
                last_checked_at=w.get("metadata", {}).get("last_checked_at", None),
            )
            for w in content["workloads"]
        ]

        workloads.sort(
            key=lambda w: [w.last_checked_at] if w.last_checked_at is not None else [],
            reverse=True,
        )

        return workloads[:3]

    async def get_recommendations(self) -> List[Recommendation]:
        response = await self.platform_request.get(
            self.advisor_url,
            "/api/insights-results-aggregator/v2/rule?impacting=true",
            user_identity=await self.user_identity_provider.get_user_identity(),
        )
        response.raise_for_status()

        content = await response.json()

        rules = [
            Recommendation(
                id=r["rule_id"],
                description=r["description"],
                total_risk=r["total_risk"],
            )
            for r in content["recommendations"]
        ]
        rules.sort(key=lambda r: r.total_risk, reverse=True)

        return rules[:3]
