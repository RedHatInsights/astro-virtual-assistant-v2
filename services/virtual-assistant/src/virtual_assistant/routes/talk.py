import logging
from typing import Optional, List, Union, Tuple, Any
from werkzeug.exceptions import BadRequest

import injector
from common.session_storage import SessionStorage, Session
from ibm_cloud_sdk_core.api_exception import ApiException
from quart import Blueprint, request
from quart_schema import validate_request, validate_response
from pydantic import BaseModel


from common.auth import (
    assistant_user_id,
    require_identity_header,
    decoded_identity_header,
)
from common.types.errors import ValidationError
from virtual_assistant.assistant import Assistant, AssistantContext, Response, AssistantInput, Query
from virtual_assistant.assistant.response_processor.response_processor import (
    ResponseProcessor,
)


blueprint = Blueprint("talk", __name__, url_prefix="/talk")

logger = logging.getLogger(__name__)


class TalkInput(BaseModel):
    """Input elements to pass to the assistant"""

    text: str
    """User text to send to the assistant."""

    option_id: Optional[str] = None
    """Option id to use"""


class TalkRequest(BaseModel):
    """Request data for talk endpoint."""

    session_id: Optional[str] = None
    """User session id. Do not send if we want to start a new session"""

    input: TalkInput
    """User input"""

    include_debug: Optional[bool] = False
    """Include debug information in the output"""


class TalkResponse(BaseModel):
    session_id: str
    """User session id to use for the following requests"""

    response: List[Response]
    """List of responses given by the assistant"""

    debug_output: Optional[dict[str, Any]] = None
    """Debug output returned if specified - This will include details the assistant went on when fulfilling the request"""


@blueprint.route("", methods=["POST"])
@require_identity_header
@validate_request(TalkRequest)
@validate_response(TalkResponse, 200)
@validate_response(ValidationError, 400)
async def talk(
    data: TalkRequest,
    assistant: injector.Inject[Assistant],
    session_storage: injector.Inject[SessionStorage],
    assistant_response_processors: injector.Inject[List[ResponseProcessor]],
) -> Union[TalkResponse, Tuple[ValidationError, 400]]:
    identity = request.headers.get("x-rh-identity")
    user_id = assistant_user_id(identity)
    session_id = data.session_id

    debug_output = None
    if data.include_debug:
        debug_output = {}

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
        query = Query(
            text=data.input.text,
            option_id=data.input.option_id,
        )

        identity_json = decoded_identity_header(identity)["identity"]
        assistant_response = await assistant.send_message(
            message=AssistantInput(
                session_id=session_id,
                user_id=user_id,
                query=query,
                include_debug=data.include_debug,
            ),
            context=AssistantContext(
                is_internal=identity_json.get("user", {}).get("is_internal", False),
                is_org_admin=identity_json.get("user", {}).get("is_org_admin", False),
            ),
        )

        if data.include_debug:
            debug_output["assistant"] = assistant_response.debug_output

        if assistant_response_processors:
            for processor in assistant_response_processors:
                assistant_response.response = await processor.process(
                    assistant_response.response, query=query
                )

    except ApiException as e:
        # Todo: Should we just let raise this error and let the error handler wrap it into a validation error?
        return ValidationError(message=str(e)), 400

    return TalkResponse(
        session_id=session_id,
        response=assistant_response.response,
        debug_output=debug_output,
    )
