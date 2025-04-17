import injector
from pydantic import BaseModel
from typing import List

from quart import Blueprint, render_template
from quart_schema import validate_response, validate_querystring, document_headers

from watson_extension.core.platform.notifications import (
    NotificationsBundle,
    NotificationEventInfo,
    PlatformNotificationsCore,
)
from watson_extension.routes import RHSessionIdHeader


blueprint = Blueprint("notifications", __name__, url_prefix="/notifications")


class NotificationsEventOptionsRequestQuery(BaseModel):
    bundle_name: NotificationsBundle


class NotificationsEventOptionsResponse(BaseModel):
    options: List[NotificationEventInfo]


class RemoveBehaviorGroupRequestQuery(BaseModel):
    bundle_id: str
    event_id: str
    event_application_display_name: str


class RemoveBehaviorGroupResponse(BaseModel):
    response: str


@blueprint.get("/notifications_event/options")
@validate_querystring(NotificationsEventOptionsRequestQuery)
@validate_response(NotificationsEventOptionsResponse)
@document_headers(RHSessionIdHeader)
async def notifications_event_options(
    query_args: NotificationsEventOptionsRequestQuery,
    platform_notifications_service: injector.Inject[PlatformNotificationsCore],
) -> NotificationsEventOptionsResponse:
    notifications_event_options = (
        await platform_notifications_service.get_notifications_event_options(
            query_args.bundle_name
        )
    )

    return NotificationsEventOptionsResponse(options=notifications_event_options)


@blueprint.get("/remove_behavior_group")
@validate_querystring(RemoveBehaviorGroupRequestQuery)
@validate_response(RemoveBehaviorGroupResponse)
@document_headers(RHSessionIdHeader)
async def remove_behavior_group(
    query_args: RemoveBehaviorGroupRequestQuery,
    platform_notifications_service: injector.Inject[PlatformNotificationsCore],
) -> RemoveBehaviorGroupResponse:
    remove_behavior_group_response = (
        await platform_notifications_service.remove_behaviour_group(
            query_args.bundle_id, query_args.event_id
        )
    )

    return RemoveBehaviorGroupResponse(
        response=await render_template(
            "platform/notifications/remove_behavior_group.txt.jinja",
            response_type=remove_behavior_group_response.value,
            event=query_args.event_application_display_name,
        )
    )
