import uuid

from . import Assistant, AssistantInput, AssistantOutput, ResponseText


class EchoAssistant(Assistant):
    async def create_session(self, user_id: str) -> str:
        return uuid.uuid4().__str__()

    async def send_message(self, message: AssistantInput) -> AssistantOutput:
        return AssistantOutput(
            session_id=message.session_id,
            user_id=message.user_id,
            response=[
                ResponseText(
                    text=message.query.text,
                ),
            ],
        )
