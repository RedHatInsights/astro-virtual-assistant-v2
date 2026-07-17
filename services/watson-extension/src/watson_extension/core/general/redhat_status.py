import enum
from dataclasses import dataclass
from typing import List, Tuple

import injector

from watson_extension.clients.general.redhat_status import RedhatStatusClient


class ServicesOfflineResponseTypes(enum.Enum):
    ERROR = "error"
    INCIDENT_EXISTS = "incident_exists"
    NO_INCIDENTS = "no_incidents"


@dataclass
class IncidentType:
    name: str
    status: str


class RedhatStatusCore:
    def __init__(
        self,
        redhat_status_client: injector.Inject[RedhatStatusClient],
    ):
        self.redhat_status_client = redhat_status_client

    async def check_services_offline(
        self,
    ) -> Tuple[ServicesOfflineResponseTypes, List[IncidentType], str]:
        content = await self.redhat_status_client.check_services_offline()

        if not content:
            return ServicesOfflineResponseTypes.ERROR, [], "0"

        incidents = content["incidents"]

        if incidents:
            casted_incidents = [
                IncidentType(name=incident["name"], status=incident["status"])
                for incident in incidents
            ]
            count = str(len(incidents))
            return ServicesOfflineResponseTypes.INCIDENT_EXISTS, casted_incidents, count

        return ServicesOfflineResponseTypes.NO_INCIDENTS, [], "0"
