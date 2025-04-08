import injector
import uuid
from datetime import datetime

from watson_extension.clients.insights.notifications import NotificationsClient


class NotificationsCore:
    def __init__(self, notifications_client: injector.Inject[NotificationsClient]):
        self.notifications_client = notifications_client

    async def send_rbac_request_admin(
        self,
        org_id: str,
        username: str,
        user_email: str,
        user_message: str,
        requested_url: str,
    ):
        event = dict(
            {
                "id": str(uuid.uuid4()),
                "bundle": "console",
                "application": "rbac",
                "event_type": "request-access",
                "timestamp": datetime.now().isoformat(),
                "org_id": org_id,
                "context": {},
                "events": [
                    {
                        "metadata": {},
                        "payload": {
                            "url_path": requested_url,
                            "username": username,
                            "user": {"email": user_email, "request": user_message},
                        },
                    }
                ],
                "recipients": [{"only_admins": True}],
            }
        )

        return await self.notifications_client.send_notification(event)
