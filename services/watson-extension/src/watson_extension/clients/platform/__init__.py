from dataclasses import dataclass


@dataclass
class IntegrationInfo:
    name: str
    enabled: bool
    type: str
    group: str
    id: str
