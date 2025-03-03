from . import Assistant, AssistantResponse, AssistantInput
from virtual_assistant.api_types import TalkResponse


class EchoAssistant(Assistant):
    async def send_message(
        self, session_id: str, user_id: str, message: AssistantInput
    ) -> AssistantResponse:
        return TalkResponse(
            session_id="echo-session",
            response=[
                {
                    "text": message["text"],
                }
            ],
        )
