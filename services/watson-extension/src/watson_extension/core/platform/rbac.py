from typing import Any, Dict, List, Tuple
import injector

from watson_extension.clients.platform.rbac import (
    RBACClient,
    Roles,
    TAMRequestAccessPayload,
)

_DURATIONS = ["3 days", "1 week", "2 weeks"]


class RBACCore:
    def __init__(self, rbac_client: injector.Inject[RBACClient]):
        self.rbac_client = rbac_client

    async def get_roles_for_tam(self) -> List[Dict[str, Any]]:
        return await self.rbac_client.get_roles_for_tam()

    async def send_rbac_tam_request(
        self, account_id, org_id, start_date, end_date, roles
    ) -> bool:
        return await self.rbac_client.send_rbac_tam_request(
            TAMRequestAccessPayload(
                account_id=account_id,
                org_id=org_id,
                start_date=start_date,
                end_date=end_date,
                roles=_get_roles_names(roles),
            )
        )

    def get_start_end_date_from_duration(self, duration: str) -> Tuple[str, str]:
        from datetime import date, timedelta

        start_date = date.today()
        duration_map = {
            "3 days": timedelta(days=3),
            "1 week": timedelta(weeks=1),
            "2 weeks": timedelta(weeks=2),
        }
        end_date = start_date + duration_map.get(duration, timedelta(0))

        return start_date.strftime("%m/%d/%Y"), end_date.strftime("%m/%d/%Y")


def _get_roles_names(roles: List[Roles]):
    return [role.display_name for role in roles]
