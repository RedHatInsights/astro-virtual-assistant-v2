import enum
from typing import Optional

import injector

from watson_extension.clients.insights.rhsm import RhsmClient

class InventoryCore:
    def __init__(self, rhsm_client: injector.Inject[RhsmClient]):
        self.rhsm_client = rhsm_client

    async def create_activation_keys(self, name: str):
        return await self.rhsm_client.create_activation_key(name)
