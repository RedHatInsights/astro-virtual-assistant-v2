import abc
import injector
import logging
from dataclasses import dataclass
from typing import Any, Dict, List

from common.identity import AbstractUserIdentityProvider
from common.platform_request import AbstractPlatformRequest
from watson_extension.clients import RbacURL
from watson_extension.config import is_running_locally


logger = logging.getLogger(__name__)


@dataclass
class Roles:
    uuid: str
    name: str
    display_name: str
    description: str
    created: str
    modified: str
    policyCount: int
    groups_in_count: int
    accessCount: int
    applications: List[str]
    system: bool
    platform_default: bool
    admin_default: bool
    external_role_id: str = None
    external_tenant: str = None


@dataclass
class TAMRequestAccessPayload:
    account_id: str
    org_id: str
    start_date: str
    end_date: str
    roles: List[str]


class RBACClient(abc.ABC):
    @abc.abstractmethod
    async def get_roles_for_tam(self) -> List[Roles]: ...

    async def send_rbac_tam_request(self, body: Dict[str, Any]): ...


class RBACClientHttp(RBACClient):
    def __init__(
        self,
        rbac_url: injector.Inject[RbacURL],
        user_identity_provider: injector.Inject[AbstractUserIdentityProvider],
        platform_request: injector.Inject[AbstractPlatformRequest],
    ):
        super().__init__()
        self.rbac_url = rbac_url
        self.user_identity_provider = user_identity_provider
        self.platform_request = platform_request

    async def get_roles_for_tam(self) -> List[Roles]:
        """Get roles for TAM"""
        response = await self.platform_request.get(
            self.rbac_url,
            "/api/rbac/v1/roles/?system=true&limit=9999&order_by=display_name&add_fields=groups_in_count",
            user_identity=await self.user_identity_provider.get_user_identity(),
        )
        response.raise_for_status()
        return [
            Roles(
                uuid=role["uuid"],
                name=role["name"],
                display_name=role["display_name"],
                description=role["description"],
                created=role["created"],
                modified=role["modified"],
                policyCount=role["policyCount"],
                groups_in_count=role["groups_in_count"],
                accessCount=role["accessCount"],
                applications=role["applications"],
                system=role["system"],
                platform_default=role["platform_default"],
                admin_default=role["admin_default"],
                external_role_id=role.get("external_role_id"),
                external_tenant=role.get("external_tenant"),
            )
            for role in response.json()
        ]

    async def send_rbac_tam_request(self, body: TAMRequestAccessPayload):
        if is_running_locally:
            logger.info(
                f"Called send_rbac_tam_request in local environment with body: {body}"
            )

            from unittest.mock import Mock

            mock_response = Mock()
            mock_response.ok = True

            return mock_response

        # POST https://console.stage.redhat.com/api/rbac/v1/cross-account-requests/
        return await self.platform_request.post(
            self.rbac_url,
            "/api/rbac/v1/cross-account-requests/",
            user_identity=await self.user_identity_provider.get_user_identity(),
            json=body,
        )
