import enum
from dataclasses import dataclass
from typing import List

import injector

from watson_extension.clients.openshift.advisor import AdvisorClient


class RecommendationCategory(enum.Enum):
    """
    Categories to group different searching queries for rhel advisor recommendations
    """

    RECOMMENDATION = "recommendation"
    CLUSTER = "cluster"
    WORKLOAD = "workload"


@dataclass
class Recommendation:
    description: str
    link: str


@dataclass
class AdvisorRecommendationResponse:
    category: RecommendationCategory
    dashboard_link: str
    recommendations: List[Recommendation]


class AdvisorCore:
    def __init__(self, advisor_client: injector.Inject[AdvisorClient]):
        self.advisor_client = advisor_client

    async def get_recommendations(
        self, category_type: RecommendationCategory
    ) -> AdvisorRecommendationResponse:
        if category_type == RecommendationCategory.RECOMMENDATION:
            recommendations = await self.advisor_client.get_recommendations()
            return AdvisorRecommendationResponse(
                category=category_type,
                dashboard_link="/openshift/insights/advisor/recommendations",
                recommendations=[
                    Recommendation(
                        description=r.description,
                        link=f"/openshift/insights/advisor/recommendations/{r.id}",
                    )
                    for r in recommendations
                ],
            )
        elif category_type == RecommendationCategory.CLUSTER:
            clusters = await self.advisor_client.get_clusters()
            return AdvisorRecommendationResponse(
                category=category_type,
                dashboard_link="/openshift/insights/advisor/clusters",
                recommendations=[
                    Recommendation(
                        description=c.name,
                        link=f"/openshift/insights/advisor/clusters/{c.id}",
                    )
                    for c in clusters
                ],
            )
        elif category_type == RecommendationCategory.WORKLOAD:
            workloads = await self.advisor_client.get_workloads()
            return AdvisorRecommendationResponse(
                category=category_type,
                dashboard_link="/openshift/insights/advisor/workloads",
                recommendations=[
                    Recommendation(
                        description=w.cluster_display_name,
                        link=f"/openshift/insights/advisor/workloads/{w.cluster_id}/{w.namespace_id}",
                    )
                    for w in workloads
                ],
            )
        else:
            raise RuntimeError(
                f"Unexpected openshift advisor recommendation type: {category_type}"
            )
