import json
import textwrap
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import MagicMock
from .. import get_resource_contents

import pytest

from virtual_assistant.assistant import (
    AssistantInput,
    AssistantContext,
    Query,
    ResponseType,
    OptionsType,
)
from virtual_assistant.assistant.watson import (
    WatsonAssistant,
    build_assistant,
    format_response,
    get_feedback_command_params,
    get_service_account_command_params,
    WatsonAssistantVariables,
)
from ibm_watson import AssistantV2
from ibm_watson.assistant_v2 import (
    MessageInput,
    MessageInputOptions,
    MessageContext,
    MessageContextSkills,
    MessageContextActionSkill,
)
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
    return WatsonAssistant(
        assistant_v2, assistant_id, environment_id, WatsonAssistantVariables()
    )


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
        ),
        context=AssistantContext(
            is_internal=False, is_org_admin=False, user_email="user@example.com"
        ),
    )
    assistant_v2.message.assert_called_once()
    assistant_v2.message.assert_called_with(
        assistant_id=assistant_id,
        environment_id=environment_id,
        session_id="1234",
        user_id="1234",
        input=MessageInput(
            message_type="text",
            text="hello world",
            options=MessageInputOptions(
                export=True,
            ),
        ),
        context=MessageContext(
            skills=MessageContextSkills(
                actions_skill=MessageContextActionSkill(
                    skill_variables={
                        "Draft": True,
                        "IsInternal": False,
                        "IsOrgAdmin": False,
                    }
                )
            )
        ),
    )


@given(st.booleans())
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)  # The fixtures are not being reset per call, but is fine for this test
async def test_send_draft_variable(
    watson, assistant_v2, assistant_id, environment_id, draft_value
):
    watson.variables.draft = draft_value
    await watson.send_message(
        message=AssistantInput(
            session_id="1234", user_id="1234", query=Query(text="hello world")
        ),
        context=AssistantContext(
            is_internal=False, is_org_admin=False, user_email="user@example.com"
        ),
    )
    context = assistant_v2.message.call_args.kwargs["context"]
    assert context.skills.actions_skill.skill_variables["Draft"] is draft_value


@given(st.booleans(), st.booleans())
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_send_assistant_context(
    watson, assistant_v2, assistant_id, environment_id, is_internal, is_org_admin
):
    watson.variables.draft = True
    await watson.send_message(
        message=AssistantInput(
            session_id="1234", user_id="1234", query=Query(text="hello world")
        ),
        context=AssistantContext(
            is_internal=is_internal,
            is_org_admin=is_org_admin,
            user_email="user@example.com",
        ),
    )
    context = assistant_v2.message.call_args.kwargs["context"]
    assert context.skills.actions_skill.skill_variables["IsInternal"] is is_internal
    assert context.skills.actions_skill.skill_variables["IsOrgAdmin"] is is_org_admin


async def test_get_feedback_command_params():
    watson_message = """/feedback <|start_feedback_type|>bug<|end_feedback_type|>
    <|start_feedback_response|>Whoa! Just found this bug!<|end_feedback_response|>
    <|start_usability_study|>true<|end_usability_study|>
    """

    extracted_args = get_feedback_command_params(watson_message, "user@example.com")
    summary = extracted_args[0]
    description = extracted_args[1]
    labels = extracted_args[2]

    expected_description = textwrap.dedent("""
    Feedback type: bug
    Feedback: Whoa! Just found this bug!

    The user wants to participate in a usability study. Email: user@example.com
    """)

    assert summary == "Platform feedback from the assistant"
    assert description == expected_description
    assert labels == "virtual-assistant,bug-feedback"


async def test_get_service_account_command_params():
    watson_message = """/create_service_account
    <|start_name|>test1<|end_name|>
    <|start_description|>Now, provide a short description for your service account.<|end_description|>
    <|start_environment|>stage<|end_environment|>
    """

    extracted_args = get_service_account_command_params(watson_message)
    name = extracted_args[0]
    description = extracted_args[1]
    environment = extracted_args[2]

    assert name == "test1"
    assert description == "Now, provide a short description for your service account."
    assert environment == "stage"


async def test_get_service_account_command_params_missing_tag():
    # Test when the <|name|> tag is missing.
    watson_message_missing_name = """/create_service_account
    <|start_description|>Now, provide a short description for your service account.<|end_description|>
    <|start_environment|>stage<|end_environment|>
    """
    with pytest.raises(ValueError):
        get_service_account_command_params(watson_message_missing_name)


async def test_format_response():
    formatted = format_response(
        json.loads(get_resource_contents("watson_format.json")), "user@example.com"
    )
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
    assert formatted[2].options[0].option_id is None
    assert formatted[2].options[1].text == "last resort"
    assert formatted[2].options[1].value == "run"
    assert formatted[2].options[1].option_id is None

    assert formatted[3].type == ResponseType.OPTIONS
    assert formatted[3].options_type == OptionsType.DROPDOWN
    assert formatted[3].text is None
    assert len(formatted[3].options) == 1
    assert formatted[3].options[0].text == "no pref"
    assert formatted[3].options[0].value == "none"
    assert formatted[3].options[0].option_id is None

    assert formatted[4].type == ResponseType.OPTIONS
    assert formatted[4].options_type is None
    assert formatted[4].text is None
    assert len(formatted[4].options) == 1
    assert formatted[4].options[0].text == "no title"
    assert formatted[4].options[0].value == "without it"
    assert formatted[4].options[0].option_id is None

    assert formatted[5].type == ResponseType.OPTIONS
    assert formatted[5].options_type == OptionsType.SUGGESTION
    assert formatted[5].text == "What do you mean?"
    assert len(formatted[5].options) == 2
    assert formatted[5].options[0].text == "maybe"
    assert formatted[5].options[0].value == "suggest"
    assert (
        formatted[5].options[0].option_id
        == '[{"intent": "some-intent", "confidence": 1}]'
    )
    assert formatted[5].options[1].text == "no-id"
    assert formatted[5].options[1].value == "no-id-provided"
    assert formatted[5].options[1].option_id is None
    assert len(formatted[5].channels) == 1
    assert formatted[5].channels[0] == "console"

    assert formatted[6].type == ResponseType.PAUSE
    assert formatted[6].time == 3000
    assert formatted[6].is_typing is True
    assert len(formatted[6].channels) == 2
    assert formatted[6].channels[0] == "console"
    assert formatted[6].channels[1] == "slack"
