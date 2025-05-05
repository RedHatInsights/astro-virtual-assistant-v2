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
        result = await self.redhat_status_client.check_services_offline()
        if not result.ok:
            return ServicesOfflineResponseTypes.ERROR, [], "0"

        content = await result.json()

        incidents = content["incidents"]
        count = str(len(incidents))
        if incidents and count != "0":
            casted_incidents = [
                IncidentType(name=incident["name"], status=incident["status"])
                for incident in incidents
            ]
            return ServicesOfflineResponseTypes.INCIDENT_EXISTS, casted_incidents, count

        return ServicesOfflineResponseTypes.NO_INCIDENTS, [], "0"
