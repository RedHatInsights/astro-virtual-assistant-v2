from typing import Any, Dict, List, Tuple
import injector
from aiohttp import ClientResponse

from watson_extension.clients.platform.rbac import RBACClient, Roles, TAMRequestAccessPayload

_DURATIONS = ["3 days", "1 week", "2 weeks"]

class RBACCore:
    def __init__(self, rbac_client: injector.Inject[RBACClient]):
        self.rbac_client = rbac_client

    async def get_roles_for_tam(self) -> List[Dict[str, Any]]:
        return await self.rbac_client.get_roles_for_tam()
    
    async def send_rbac_tam_request(self, account_id, org_id, start_date, end_date, roles) -> ClientResponse:
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
        end_date = start_date

        if duration == "3 days":
            end_date += timedelta(days=3)
        elif duration == "1 week":
            end_date += timedelta(weeks=1)
        elif duration == "2 weeks":
            end_date += timedelta(weeks=2)

        return start_date.strftime("%m/%d/%Y"), end_date.strftime("%m/%d/%Y")


def _get_roles_names(roles: List[Roles]):
    return [role.display_name for role in roles]
