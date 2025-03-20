import abc
from dataclasses import dataclass
from typing import Optional, List

import injector

from watson_extension.clients import RhsmURL
from watson_extension.clients.identity import AbstractUserIdentityProvider
from watson_extension.clients.platform_request import AbstractPlatformRequest


@dataclass
class SubscriptionInfo:
    number: int
    category: str


class RhsmClient(abc.ABC):
    @abc.abstractmethod
    async def check_subscriptions(
        self, category: Optional[str]
    ) -> List[SubscriptionInfo]: ...


class RhsmClientHttp(RhsmClient):
    def __init__(
        self,
        rhsm_url: injector.Inject[RhsmURL],
        user_identity_provider: injector.Inject[AbstractUserIdentityProvider],
        platform_request: injector.Inject[AbstractPlatformRequest],
    ):
        super().__init__()
        self.rhsm_url = rhsm_url
        self.user_identity_provider = user_identity_provider
        self.platform_request = platform_request

    async def check_subscriptions(
        self,
        category: Optional[str],
    ) -> List[SubscriptionInfo]:
        request = "/api/rhsm/v2/products/status"
        response = await self.platform_request.get(
            self.rhsm_url,
            request,
            user_identity=await self.user_identity_provider.get_user_identity(),
        )
        response.raise_for_status()

        content = await response.json()
        content_body = content.get("body")

        subscriptions_info = []
        if content_body:
            if category:
                category_text = category
                if category == "expiringSoon":
                    category_text = "expiring"

                subs_category_count = content_body.get(category)
                subscriptions_info.append(
                    SubscriptionInfo(number=subs_category_count, category=category_text)
                )
            else:
                subscriptions_info = []
                if content_body.get("active"):
                    subscriptions_info.append(
                        SubscriptionInfo(
                            number=content_body["active"], category="active"
                        )
                    )
                if content_body.get("expiringSoon"):
                    subscriptions_info.append(
                        SubscriptionInfo(
                            number=content_body["expiringSoon"], category="expiring"
                        )
                    )
                if content_body.get("expired"):
                    subscriptions_info.append(
                        SubscriptionInfo(
                            number=content_body["expired"], category="expired"
                        )
                    )

        return subscriptions_info
