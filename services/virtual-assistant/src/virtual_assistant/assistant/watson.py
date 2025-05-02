import asyncio
import dataclasses
import json
import re
import textwrap
from typing import List, Any, Tuple

from . import (
    Assistant,
    AssistantContext,
    AssistantInput,
    AssistantOutput,
    Response as AssistantResponse,
    ResponseCommand,
    ResponseText,
    ResponseOption,
    ResponseOptions,
    OptionsType,
    ResponsePause,
)
from ibm_watson import AssistantV2
from ibm_watson.assistant_v2 import RuntimeIntent
from ibm_watson.assistant_v2 import (
    MessageInput,
    MessageContext,
    MessageContextSkills,
    MessageContextActionSkill,
)
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

_WATSON_DRAFT_ENVIRONMENT_VARIABLE = "Draft"
_WATSON_IS_INTERNAL_ENVIRONMENT_VARIABLE = "IsInternal"
_WATSON_IS_ORG_ADMIN_ENVIRONMENT_VARIABLE = "IsOrgAdmin"


def build_assistant(api_key: str, env_version: str, api_url: str) -> AssistantV2:
    """Authentication for watson assistant"""
    authenticator = IAMAuthenticator(api_key)
    assistant = AssistantV2(version=env_version, authenticator=authenticator)
    assistant.set_service_url(api_url)
    return assistant


def get_debug_output(response: dict) -> dict[str, Any]:
    output = response.get("output", {})
    return {
        "entities": output.get("entities", []),
        "intents": output.get("intents", []),
    }


def search_for_field(
    tag: str, watson_msg: str, regex_flags: re.RegexFlag = 0, default: str = None
) -> str:
    pattern = rf"<\|start_{tag}\|>(.*?)<\|end_{tag}\|>"
    match = re.search(pattern, watson_msg, regex_flags)
    if match:
        return match.group(1)
    if default:
        return default

    raise ValueError(f"Missing {tag} in the message: {watson_msg}")


def get_feedback_command_params(
    watson_msg: str, user_email: str
) -> Tuple[str, str, str]:
    """
    Extracts the params from the message of the feedback command.

    Example feedback command and params:
    /feedback <|start_feedback_type|>bug<|end_feedback_type|>
    <|start_feedback_response|>This is a user feedback<|end_feedback_response|>
    <|start_usability_study|>false<|end_usability_study|>
    """

    feedback_type = search_for_field("feedback_type", watson_msg, default="general")
    feedback_response = search_for_field(
        "feedback_response", watson_msg, default="", regex_flags=re.DOTALL
    )
    usability_study = search_for_field("usability_study", watson_msg, default="false")

    feedback_type_label = f"{feedback_type}-feedback"

    feedback_usability_study = (
        "The user DOES NOT want to participate in our usability studies."
    )
    if usability_study:
        feedback_usability_study = (
            f"The user wants to participate in a usability study. Email: {user_email}"
        )

    summary = "Platform feedback from the assistant"
    description = textwrap.dedent(f"""
    Feedback type: {feedback_type}
    Feedback: {feedback_response}

    {feedback_usability_study}
    """)
    labels = f"virtual-assistant,{feedback_type_label}"

    return [summary, description, labels]


def get_service_account_command_params(watson_msg: str) -> Tuple[str, str, str]:
    """
    Extracts the params from the message of the service account command.

    Example feedback command and params:
    /create_service_account
    <|start_name|>test1<|end_name|>
    <|start_description|>Now, provide a short description for your service account.<|end_description|>
    <|start_environment|>stage<|end_environment|>
    """
    name = search_for_field("name", watson_msg)
    description = search_for_field("description", watson_msg)
    environment = search_for_field("environment", watson_msg)

    return [name, description, environment]


def format_response(response: dict, user_email: str) -> List[AssistantResponse]:
    """Formats the message response from watson and maps it to the VA API response for the user

    Parameters:
    session_id: The watson assistant session_id
    response: The response to send_watson_message received from watson

    Returns:
    TalkResponse: The truncated watson message response information to be sent to the user
    """
    watson_generic = response["output"]["generic"]
    assistant_response: List[AssistantResponse] = []

    for generic in watson_generic:
        entry = None

        if generic["response_type"] == "text":
            if generic["text"].startswith("/"):  # command message
                params = generic["text"].split(" ")
                command = params[0].strip("/")
                if command == "feedback":
                    feedback_params = get_feedback_command_params(
                        generic["text"], user_email
                    )
                    entry = ResponseCommand(command=command, args=feedback_params)
                elif command == "create_service_account":
                    service_account_params = get_service_account_command_params(
                        generic["text"]
                    )
                    entry = ResponseCommand(
                        command=command, args=service_account_params
                    )
                else:
                    entry = ResponseCommand(command=command, args=params[1:])
            else:
                entry = ResponseText(
                    text=generic["text"],
                )

        if generic["response_type"] == "option":
            options: List[ResponseOption] = []
            for option in generic["options"]:
                options.append(
                    ResponseOption(
                        text=option["label"],
                        value=option["value"].get("input").get("text"),
                    )
                )

            options_type = None
            if "preference" in generic:
                if generic["preference"] == "dropdown":
                    options_type = OptionsType.DROPDOWN
                elif generic["preference"] == "button":
                    options_type = OptionsType.BUTTON

            entry = ResponseOptions(
                text=generic.get("title", None),
                options=options,
                options_type=options_type,
            )

        if generic["response_type"] == "suggestion":
            options: List[ResponseOption] = []
            for suggestion in generic["suggestions"]:
                option = ResponseOption(
                    text=suggestion["label"],
                    value=suggestion["value"].get("input").get("text"),
                )

                intents = suggestion["value"].get("input").get("intents")
                if intents:
                    option.option_id = json.dumps(intents)

                options.append(option)

            entry = ResponseOptions(
                text=generic.get("title", None),
                options=options,
                options_type=OptionsType.SUGGESTION,
            )
        if generic["response_type"] == "pause":
            entry = ResponsePause(time=generic["time"], is_typing=generic["typing"])

        if entry is not None:
            channels = generic.get("channels", None)
            if channels is not None:
                entry.channels = []
                for channel in channels:
                    entry.channels.append(channel["channel"])

            assistant_response.append(entry)

    return assistant_response


@dataclasses.dataclass
class WatsonAssistantVariables:
    draft: bool = True


class WatsonAssistant(Assistant):
    def __init__(
        self,
        assistant: AssistantV2,
        assistant_id: str,
        environment_id: str,
        variables: WatsonAssistantVariables,
    ):
        super().__init__()
        self.assistant = assistant
        self.assistant_id = assistant_id
        self.environment_id = environment_id
        self.variables = variables

    async def create_session(self, user_id: str) -> str:
        """Creates a watson assistant session if the provided session id is None

        Parameters:
        session_id: The watson assistant session id

        Returns:
        str: A valid session id
        """
        response = await asyncio.to_thread(
            self.assistant.create_session, assistant_id=self.environment_id
        )
        return response.get_result()["session_id"]

    async def send_message(
        self, message: AssistantInput, context: AssistantContext
    ) -> AssistantOutput:
        sanitized_text = re.sub("\s+", " ", message.query.text).strip()
        message_input = MessageInput(message_type="text", text=sanitized_text)
        if message.query.option_id:
            intents_array = json.loads(message.query.option_id)
            message_input.intents = [
                RuntimeIntent(intent=i.get("intent"), confidence=i.get("confidence"))
                for i in intents_array
            ]

        response = await asyncio.to_thread(
            self.assistant.message,
            assistant_id=self.assistant_id,
            environment_id=self.environment_id,
            session_id=message.session_id,
            user_id=message.user_id,
            input=message_input,
            context=MessageContext(
                skills=MessageContextSkills(
                    actions_skill=MessageContextActionSkill(
                        skill_variables={
                            _WATSON_DRAFT_ENVIRONMENT_VARIABLE: self.variables.draft,
                            _WATSON_IS_INTERNAL_ENVIRONMENT_VARIABLE: context.is_internal,
                            _WATSON_IS_ORG_ADMIN_ENVIRONMENT_VARIABLE: context.is_org_admin,
                        }
                    )
                )
            ),
        )

        response_result = response.get_result()

        debug_output = None
        if message.include_debug:
            debug_output = get_debug_output(response_result)

        return AssistantOutput(
            session_id=message.session_id,
            user_id=message.user_id,
            response=format_response(response_result, context.user_email),
            debug_output=debug_output,
        )
