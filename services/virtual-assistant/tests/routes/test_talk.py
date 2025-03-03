from unittest.mock import MagicMock
from quart.typing import TestClientProtocol
import injector
import pytest

from virtual_assistant.routes.talk import blueprint
from virtual_assistant.assistant.watson import WatsonAssistant
from virtual_assistant.assistant import Assistant
from virtual_assistant.api_types import TalkResponse
from .. import async_value

from .common import app_with_blueprint


@pytest.fixture
async def watson() -> MagicMock:
    return MagicMock(WatsonAssistant)


@pytest.fixture
async def test_client(watson) -> TestClientProtocol:
    def injector_binder(binder: injector.Binder):
        binder.bind(Assistant, watson)

    return app_with_blueprint(blueprint, injector_binder).test_client()


async def test_talk(test_client, watson) -> None:
    watson.send_message = MagicMock(
        return_value=async_value(TalkResponse(session_id="x", response=[]))
    )
    response = await test_client.post(
        "/talk",
        json={
            "session_id": "1234",
            "input": {
                "text": "hello world",
            },
        },
        headers={
            "x-rh-identity": "eyJpZGVudGl0eSI6IHsiYWNjb3VudF9udW1iZXIiOiJhY2NvdW50MTIzIiwib3JnX2lkIjoib3JnMTIzIiwidHlwZSI6IlVzZXIiLCJ1c2VyIjp7ImlzX29yZ19hZG1pbiI6dHJ1ZSwgInVzZXJfaWQiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOiJhc3RybyJ9LCJpbnRlcm5hbCI6eyJvcmdfaWQiOiJvcmcxMjMifX19",
        },
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == []
