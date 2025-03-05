import logging
from typing import Optional
from werkzeug.exceptions import BadRequest

import injector
from common.session_storage import SessionStorage, Session
from ibm_cloud_sdk_core.api_exception import ApiException
from quart import Blueprint, request
from quart_schema import validate_request, validate_response
from pydantic import BaseModel


from common.auth import assistant_user_id, require_identity_header
from common.types.errors import ValidationError
from virtual_assistant.assistant import Assistant, Response, AssistantInput, Query

blueprint = Blueprint("talk", __name__, url_prefix="/talk")

logger = logging.getLogger(__name__)


class TalkInput(BaseModel):
    """Input elements to pass to the assistant"""

    text: str
    """User text to send to the assistant."""
    # More elements can be added if we will support additional interactions


class TalkRequest(BaseModel):
    """Request data for talk endpoint."""

    session_id: Optional[str]
    """User session id. Do not send if we want to start a new session"""

    input: TalkInput


class TalkResponse(BaseModel):
    session_id: str
    response: Response


@blueprint.route("", methods=["POST"])
@require_identity_header
@validate_request(TalkRequest)
@validate_response(TalkResponse, 200)
@validate_response(ValidationError, 400)
async def talk(
    data: TalkRequest,
    assistant: injector.Inject[Assistant],
    session_storage: injector.Inject[SessionStorage],
) -> TalkResponse:
    identity = request.headers.get("x-rh-identity")
    user_id = assistant_user_id(identity)
    session_id = data.session_id

    if session_id is not None:
        session = await session_storage.get(session_id)
        if session is None or session.user_id != user_id:
            raise BadRequest(f"Invalid session {session_id}")
    else:
        session_id = await assistant.create_session(user_id)

    await session_storage.put(
        Session(
            key=session_id,
            user_identity=identity,
            user_id=user_id,
        )
    )

    # Send message to the configured assistant
    try:
        assistant_response = await assistant.send_message(
            message=AssistantInput(
                session_id=session_id,
                user_id=user_id,
                query=Query(
                    text=data.input.text,
                ),
            ),
        )
    except ApiException as e:
        # Todo: Should we just let raise this error and let the handler wrap it into a validation error?
        return ValidationError(message=e.message), 400

    # Todo: Check if this syntax is OK - should we update the return type to be Tuple[TalkResponse, 200] or
    # verify if the validate_response decorator adds the http code for us
    return TalkResponse(session_id=session_id, response=assistant_response.response)
