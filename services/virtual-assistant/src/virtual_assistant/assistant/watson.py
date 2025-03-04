import asyncio
from typing import Optional

from . import Assistant, AssistantResponse, AssistantInput
from virtual_assistant.api_types import TalkResponse
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator


def build_assistant(api_key: str, env_version: str, api_url: str) -> AssistantV2:
    """Authentication for watson assistant"""
    authenticator = IAMAuthenticator(api_key)
    assistant = AssistantV2(version=env_version, authenticator=authenticator)
    assistant.set_service_url(api_url)
    return assistant


def format_response(session_id: str, response: dict) -> AssistantResponse:
    """Formats the message response from watson and maps it to the VA API reponse for the user

    Parameters:
    session_id: The watson assistant session_id
    response: The response to send_watson_message received from watson

    Returns:
    TalkResponse: The truncated watson message response information to be sent to the user
    """
    watson_generic = response["output"]["generic"]
    normalized_watson_response = []

    for generic in watson_generic:
        if generic["response_type"] == "text":
            if generic["text"].startswith("/"):  # command message
                params = generic["text"].split(" ")
                normalized_watson_response.append(
                    {"command": {"type": params[0].strip("/"), "args": params[1:]}}
                )
            else:
                normalized_watson_response.append({"text": generic["text"]})

        if generic["response_type"] == "option":
            options = []
            for option in generic["options"]:
                options.append(
                    {
                        "label": option["label"],
                        "input": option["value"].get("input"),
                    }
                )
            normalized_watson_response.append({"options": options})

        if generic["response_type"] == "suggestion":
            options = []
            for suggestion in generic["suggestions"]:
                options.append(
                    {
                        "label": suggestion["label"],
                        "input": suggestion["value"].get("input"),
                    }
                )
            normalized_watson_response.append(
                {"text": generic["title"], "options": options}
            )

    normalized_response = {
        "session_id": session_id,
        "response": normalized_watson_response,
    }

    return TalkResponse(**normalized_response)


class WatsonAssistant(Assistant):
    def __init__(self, assistant: AssistantV2, assistant_id: str, environment_id: str):
        super().__init__()
        self.assistant = assistant
        self.assistant_id = assistant_id
        self.environment_id = environment_id

    async def ensure_session_id(self, session_id: Optional[str] = None) -> str:
        """Creates a watson assistant session if the provided session id is None

        Parameters:
        session_id: The watson assistant session id

        Returns:
        str: A valid session id
        """
        if not session_id:
            response = await asyncio.to_thread(
                self.assistant.create_session, assistant_id=self.environment_id
            )
            return response.get_result()["session_id"]

        return session_id

    async def send_message(
        self, session_id: Optional[str], user_id: str, message: AssistantInput
    ) -> AssistantResponse:
        """Send a message to watson assistant

        Parameters:
        session_id: The watson assistant session id
        user_id: Used as the user_id for watson to identify unique users (org_id in this case)
        input: The text or button message options for watson

        Returns:
        dict: The response, in dictionary type, received from watson
        """

        session_id = await self.ensure_session_id(session_id)

        response = await asyncio.to_thread(
            self.assistant.message,
            assistant_id=self.assistant_id,
            environment_id=self.environment_id,
            session_id=session_id,
            user_id=user_id,  # using org_id as user_id to identity unique users
            input=message,
        )
        return format_response(session_id, response.get_result())
