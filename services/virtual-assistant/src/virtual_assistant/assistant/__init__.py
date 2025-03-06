import enum
from abc import ABC, abstractmethod
from typing import Optional, List, Union, Any
from pydantic import BaseModel


class Query(BaseModel):
    """
    User query - it can be in the form of a text or any additional structure that we use.
    For now, it is only text.
    Not all of these might be supported by the assistant.
    """

    text: Optional[str]
    """Text query to forward to the assistant. Usually doesn't require additional context"""


class AssistantInput(BaseModel):
    """
    Vendor-agnostic input to the assistant module.
    """

    session_id: str = None
    """session id for the user"""

    user_id: str
    """User identifier"""

    query: Query


class ResponseType(enum.StrEnum):
    """Types of supported responses"""

    TEXT = "TEXT"
    PAUSE = "PAUSE"
    OPTIONS = "OPTIONS"
    COMMAND = "COMMAND"


class OptionsType(enum.StrEnum):
    BUTTON = "BUTTON"
    DROPDOWN = "DROPDOWN"
    SUGGESTION = "SUGGESTION"


class BaseResponse(BaseModel):
    """Extendable response base"""

    type: ResponseType
    """One of the supported response types"""

    channels: Optional[List[str]] = None
    """Intended channel for the response. i.e. console, slack or None to allow in all"""


class ResponseText(BaseResponse):
    """Regular text response to a question'"""

    type: ResponseType = ResponseType.TEXT
    text: str


class ResponsePause(BaseResponse):
    """Injects a pause into the interaction to simulate processing"""

    type: ResponseType = ResponseType.PAUSE
    time: int
    is_typing: bool


class ResponseOption(BaseModel):
    """Option presented to the user with the value sent if selected"""

    text: str
    """Text the user sees when having to select from multiple options"""

    value: str
    """A value that is sent back when the user selects this option"""


class ResponseOptions(BaseResponse):
    """Represents a selection the user has to make"""

    type: ResponseType = ResponseType.OPTIONS
    options_type: Optional[OptionsType] = None
    text: Optional[str]
    options: List[ResponseOption]


#
class ResponseCommand(BaseResponse):
    type: ResponseType = ResponseType.COMMAND
    command: str
    args: Optional[List[Any]]


type Response = List[
    Union[ResponseText, ResponsePause, ResponseOptions, ResponseCommand]
]


class AssistantOutput(BaseModel):
    """
    Vendor-agnostic output to the assistant module.
    """

    session_id: str
    """session id for the user"""

    user_id: str
    """User identifier"""

    response: Response
    """Responses to the user"""


class Assistant(ABC):
    @abstractmethod
    async def create_session(self, user_id: str) -> str: ...

    @abstractmethod
    async def send_message(self, message: AssistantInput) -> AssistantOutput: ...
