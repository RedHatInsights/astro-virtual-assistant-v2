import injector
import enum
from typing import Optional

from watson_extension.clients.insights.rhsm import RhsmClient


class SubscriptionsCategory(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    EXPIRINGSOON = "expiringSoon"


class RhsmCore:
    def __init__(self, rhsm_client: injector.Inject[RhsmClient]):
        self.rhsm_client = rhsm_client

    async def check_subscriptions(
        self, category: Optional[SubscriptionsCategory] = None
    ):
        if category:
            return await self.rhsm_client.check_subscriptions(category.value)
        return await self.rhsm_client.check_subscriptions(None)
