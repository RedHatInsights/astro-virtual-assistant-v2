from abc import ABC, abstractmethod
from typing import Optional

from virtual_assistant.api_types import TalkInput, TalkResponse

# Todo: We need to create a common input/response that is not tied to watson
type AssistantInput = TalkInput
type AssistantResponse = TalkResponse


class Assistant(ABC):
    @abstractmethod
    async def send_message(
        self, session_id: Optional[str], user_id: str, message: AssistantInput
    ) -> AssistantResponse: ...
