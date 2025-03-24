import enum
from typing import Optional

import injector

from watson_extension.clients.insights.inventory import InventoryClient

class InventoryCore:
    def __init__(self, inventory_client: injector.Inject[InventoryClient]):
        self.inventory_client = inventory_client

    async def create_activation_keys(self, name: str):
        return await self.inventory_client.create_activation_key(name)
