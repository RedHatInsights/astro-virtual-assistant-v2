import uuid

from . import (
    Assistant,
    AssistantInput,
    AssistantOutput,
    ResponseText,
    ResponseOptions,
    ResponseOption,
)


class EchoAssistant(Assistant):
    async def create_session(self, user_id: str) -> str:
        return uuid.uuid4().__str__()

    async def send_message(self, message: AssistantInput) -> AssistantOutput:
        if message.query.text.startswith("options"):
            return AssistantOutput(
                session_id=message.session_id,
                user_id=message.user_id,
                response=[
                    ResponseOptions(
                        text=message.query.text,
                        options=[
                            ResponseOption(text="My option 1", value="opt1"),
                            ResponseOption(
                                text="My option 2",
                                value="opt2",
                                option_id="with_option_id",
                            ),
                            ResponseOption(text="My option 3", value="opt3"),
                        ],
                    ),
                ],
            )

        if message.query.option_id:
            return AssistantOutput(
                session_id=message.session_id,
                user_id=message.user_id,
                response=[
                    ResponseText(
                        text=f"Received option_id = {message.query.option_id} and message: {message.query.text}"
                    )
                ],
            )

        return AssistantOutput(
            session_id=message.session_id,
            user_id=message.user_id,
            response=[
                ResponseText(
                    text=message.query.text,
                ),
            ],
        )
