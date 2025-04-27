import dataclasses
import enum
from abc import ABC, abstractmethod
from typing import Optional, List, Union, Any, Literal
from pydantic import BaseModel


class Query(BaseModel):
    """
    User query - it can be in the form of a text or any additional structure that we use.
    For now, it is only text.
    Not all of these might be supported by the assistant.
    """

    text: Optional[str] = None
    """Text query to forward to the assistant. Usually doesn't require additional context"""

    option_id: Optional[str] = None
    """Id of the selected option that should be used"""


class AssistantInput(BaseModel):
    """
    Vendor-agnostic input to the assistant module.
    """

    session_id: str
    """session id for the user"""

    user_id: str
    """User identifier"""

    query: Query

    include_debug: bool = False
    """Include debug option if requested"""


class ResponseType(enum.StrEnum):
    """Types of supported responses"""

    TEXT = "TEXT"
    """Used for displaying text entries"""

    PAUSE = "PAUSE"
    """Used for displaying a pause in the flow"""

    OPTIONS = "OPTIONS"
    """Used for displaying a selection"""

    COMMAND = "COMMAND"
    """Used to request the UI to execute a command"""


class OptionsType(enum.StrEnum):
    """Suggestion on how to render the options"""

    BUTTON = "BUTTON"
    """Display as buttons"""

    DROPDOWN = "DROPDOWN"
    """Display as a dropdown"""

    SUGGESTION = "SUGGESTION"
    """Display as a suggestion - similar to a button but optional"""


class BaseResponse(BaseModel):
    """Extendable response base"""

    type: ResponseType
    """One of the supported response types"""

    channels: Optional[List[str]] = None
    """Intended channel for the response. i.e. console, slack or None to allow in all"""


class ResponseText(BaseResponse):
    """Regular text response to a question'"""

    type: Literal[ResponseType.TEXT] = ResponseType.TEXT
    text: str
    """Text response from the assistant"""


class ResponsePause(BaseResponse):
    """Injects a pause into the interaction to simulate processing"""

    type: Literal[ResponseType.PAUSE] = ResponseType.PAUSE
    time: int
    """How many ms to wait for"""

    is_typing: bool
    """Should display `typing` animations"""


class ResponseOption(BaseModel):
    """Option presented to the user with the value sent if selected"""

    text: str
    """Text the user sees when having to select from multiple options"""

    value: str
    """A value that is sent back when the user selects this option"""

    option_id: Optional[str] = None
    """Id identifying this option"""


class ResponseOptions(BaseResponse):
    """Represents a selection the user has to make"""

    type: Literal[ResponseType.OPTIONS] = ResponseType.OPTIONS
    options_type: Optional[OptionsType] = None
    """Options type in case the assistant is suggesting how to render the options"""

    text: Optional[str] = None
    """Text to show before the options"""

    options: List[ResponseOption]
    """List of options to display"""


#
class ResponseCommand(BaseResponse):
    type: Literal[ResponseType.COMMAND] = ResponseType.COMMAND
    command: str
    """The command to execute"""

    args: Optional[List[Any]]
    """Arguments passed to the command"""


type Response = Union[ResponseText, ResponsePause, ResponseOptions, ResponseCommand]


class AssistantOutput(BaseModel):
    """
    Vendor-agnostic output to the assistant module.
    """

    session_id: str
    """session id for the user"""

    user_id: str
    """User identifier"""

    response: List[Response]
    """Responses to the user"""

    debug_output: Optional[dict[str, Any]] = None
    """Include debug option if requested"""


@dataclasses.dataclass
class AssistantContext:
    is_internal: bool
    is_org_admin: bool


class Assistant(ABC):
    @abstractmethod
    async def create_session(self, user_id: str) -> str: ...

    @abstractmethod
    async def send_message(self, message: AssistantInput, context: AssistantContext) -> AssistantOutput: ...
