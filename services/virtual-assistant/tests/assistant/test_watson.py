import json
from unittest.mock import MagicMock
from .. import get_resource_contents

import pytest

from virtual_assistant.assistant import AssistantInput, Query, ResponseType, OptionsType
from virtual_assistant.assistant.watson import (
    WatsonAssistant,
    build_assistant,
    format_response,
)
from ibm_watson import AssistantV2
from ibm_watson.assistant_v2 import MessageInput
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator


@pytest.fixture
def assistant_v2():
    return MagicMock()


@pytest.fixture
def assistant_id():
    return "assistant_id"


@pytest.fixture
def environment_id():
    return "environment_id"


@pytest.fixture
def watson(assistant_v2, assistant_id, environment_id) -> WatsonAssistant:
    return WatsonAssistant(assistant_v2, assistant_id, environment_id)


async def test_build_assistant():
    assistant = build_assistant("my_key", "my_version", "http://localhost")
    assert type(assistant.authenticator) is IAMAuthenticator
    assert type(assistant) is AssistantV2


async def test_create_session_without_session(watson, assistant_v2):
    create_session_return = MagicMock()
    create_session_return.get_result = MagicMock(return_value={"session_id": "1234"})
    assistant_v2.create_session = MagicMock(return_value=create_session_return)

    session_id = await watson.create_session("user")
    assert session_id == "1234"
    assistant_v2.create_session.assert_called_once()


async def test_send_watson_message(watson, assistant_v2, assistant_id, environment_id):
    await watson.send_message(
        message=AssistantInput(
            session_id="1234", user_id="1234", query=Query(text="hello world")
        )
    )
    assistant_v2.message.assert_called_once()
    assistant_v2.message.assert_called_with(
        assistant_id=assistant_id,
        environment_id=environment_id,
        session_id="1234",
        user_id="1234",
        input=MessageInput(message_type="text", text="hello world"),
    )


async def test_format_response():
    formatted = format_response(json.loads(get_resource_contents("watson_format.json")))
    assert len(formatted) == 7

    assert formatted[0].type == ResponseType.COMMAND
    assert formatted[0].command == "dostuff"
    assert len(formatted[0].args) == 3
    assert formatted[0].args[0] == "arg1"
    assert formatted[0].args[1] == "arg2"
    assert formatted[0].args[2] == "arg3"

    assert formatted[1].type == ResponseType.TEXT
    assert formatted[1].text == "regular_text"

    assert formatted[2].type == ResponseType.OPTIONS
    assert formatted[2].options_type == OptionsType.BUTTON
    assert formatted[2].text == "Choose one"
    assert len(formatted[2].options) == 2
    assert formatted[2].options[0].text == "my option 1"
    assert formatted[2].options[0].value == "fire!"
    assert formatted[2].options[1].text == "last resort"
    assert formatted[2].options[1].value == "run"

    assert formatted[3].type == ResponseType.OPTIONS
    assert formatted[3].options_type == OptionsType.DROPDOWN
    assert formatted[3].text is None
    assert len(formatted[3].options) == 1
    assert formatted[3].options[0].text == "no pref"
    assert formatted[3].options[0].value == "none"

    assert formatted[4].type == ResponseType.OPTIONS
    assert formatted[4].options_type is None
    assert formatted[4].text is None
    assert len(formatted[4].options) == 1
    assert formatted[4].options[0].text == "no title"
    assert formatted[4].options[0].value == "without it"

    assert formatted[5].type == ResponseType.OPTIONS
    assert formatted[5].options_type == OptionsType.SUGGESTION
    assert formatted[5].text is None
    assert len(formatted[5].options) == 1
    assert formatted[5].options[0].text == "maybe"
    assert formatted[5].options[0].value == "suggest"
    assert len(formatted[5].channels) == 1
    assert formatted[5].channels[0] == "console"

    assert formatted[6].type == ResponseType.PAUSE
    assert formatted[6].time == 3000
    assert formatted[6].is_typing is True
    assert len(formatted[6].channels) == 2
    assert formatted[6].channels[0] == "console"
    assert formatted[6].channels[1] == "slack"
