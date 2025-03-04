import logging

import injector
from ibm_cloud_sdk_core.api_exception import ApiException
from quart import Blueprint, request
from quart_schema import validate_request, validate_response

from common.auth import get_org_id_from_identity, require_identity_header
from common.types.errors import ValidationError
from virtual_assistant.api_types import TalkRequest, TalkResponse
from virtual_assistant.assistant import Assistant

blueprint = Blueprint("talk", __name__, url_prefix="/talk")

logger = logging.getLogger(__name__)


@blueprint.route("", methods=["POST"])
@require_identity_header
@validate_request(TalkRequest)
@validate_response(TalkResponse, 200)
@validate_response(ValidationError, 400)
async def talk(
    data: TalkRequest, assistant: injector.Inject[Assistant]
) -> TalkResponse:
    identity = request.headers.get("x-rh-identity")
    # Todo: Update to use user_id - org-id applies to multiple users
    org_id = get_org_id_from_identity(identity)

    # Todo: Get this from redis?
    session_id = data.session_id
    logger.info(f"session_id: {session_id}")

    # Send message to Watson Assistant
    try:
        response = await assistant.send_message(
            session_id=session_id,
            user_id=org_id,  # using org_id as user_id to identity unique users
            message=data.input.model_dump(exclude_none=True),
        )
    except ApiException as e:
        # Todo: Should we just let raise this error and let the handler wrap it into a validation error?
        return ValidationError(message=e.message), 400

    # Todo: Check if this syntax is OK - should we update the return type to be Tuple[TalkResponse, 200] or
    # verify if the validate_response decorator adds the http code for us
    return response, 200
