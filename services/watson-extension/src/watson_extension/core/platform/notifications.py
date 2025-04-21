import enum
from dataclasses import dataclass
from typing import Optional, List

import injector

from watson_extension.clients.platform.notifications import PlatformNotificationsClient


@dataclass
class BundleInfo:
    id: str
    name: str
    display_name: str


@dataclass
class NotificationEventInfo:
    id: str
    name: str
    display_name: str
    application_id: str
    application_name: str
    application_display_name: str
    bundle_id: str


class NotificationsBundle(enum.Enum):
    """
    Notifications bundle names such as openshift/rhel/etc
    """

    OPENSHIFT = "openshift"
    RHEL = "rhel"
    CONSOLE = "console"
    UNSURE = "unsure"


class RemoveBehaviourGroupResponse(enum.Enum):
    SUCCESS = "success"
    ERROR = "error"
    NOBEHAVIORGROUP = "no_behaviour_group"


class PlatformNotificationsCore:
    def __init__(
        self,
        platform_notifications_client: injector.Inject[PlatformNotificationsClient],
    ):
        self.platform_notifications_client = platform_notifications_client

    async def validate_notifications_bundle(
        self, provided_bundle_name: str
    ) -> Optional[BundleInfo]:
        if provided_bundle_name == "unsure":
            return BundleInfo(id="unsure", name="unsure", display_name="unsure")

        result = await self.platform_notifications_client.get_available_bundles()

        if len(result) == 0:
            return None

        for bundle in result:
            if bundle["name"] == provided_bundle_name.lower():
                return BundleInfo(
                    id=bundle["id"],
                    name=bundle["name"],
                    display_name=bundle["displayName"],
                )

        return None

    async def get_notifications_event_options(
        self, bundle: NotificationsBundle
    ) -> List[NotificationEventInfo]:
        validated_bundle = await self.validate_notifications_bundle(bundle.value)
        if not validated_bundle:
            return []

        result = (
            await self.platform_notifications_client.get_available_events_by_bundle(
                validated_bundle.id
            )
        )

        options = []
        for event in result["data"]:
            event_data = NotificationEventInfo(
                id=event["id"],
                name=event["name"],
                display_name=event["display_name"],
                application_id=event["application_id"],
                application_name=event["application"]["name"],
                application_display_name=event["application"]["display_name"],
                bundle_id=validated_bundle.id,
            )
            options.append(event_data)
        return options

    async def remove_behaviour_group(
        self, bundle_id: str, event_id: str
    ) -> RemoveBehaviourGroupResponse:
        result = await self.platform_notifications_client.get_behavior_groups(bundle_id)

        if len(result) > 0:
            response = await self.platform_notifications_client.mute_event(event_id)

            if response.ok:
                return RemoveBehaviourGroupResponse.SUCCESS
            else:
                return RemoveBehaviourGroupResponse.ERROR

        return RemoveBehaviourGroupResponse.NOBEHAVIORGROUP
