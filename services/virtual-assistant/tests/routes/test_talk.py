from unittest.mock import MagicMock

from common.session_storage import SessionStorage
from common.session_storage.memory import MemorySessionStorage
from quart.typing import TestClientProtocol
import injector
import pytest

from virtual_assistant.assistant.echo import EchoAssistant
from virtual_assistant.routes.talk import blueprint, TalkResponse
from virtual_assistant.assistant.watson import WatsonAssistant
from virtual_assistant.assistant import Assistant, ResponseType

from .common import app_with_blueprint


@pytest.fixture
async def watson() -> MagicMock:
    return MagicMock(WatsonAssistant)


@pytest.fixture
async def test_client() -> TestClientProtocol:
    def injector_binder(binder: injector.Binder):
        binder.bind(Assistant, EchoAssistant())
        binder.bind(SessionStorage, MemorySessionStorage())

    return app_with_blueprint(blueprint, injector_binder).test_client()


async def test_talk(test_client) -> None:
    raw_response = await test_client.post(
        "/talk",
        json={
            "session_id": None,
            "input": {
                "text": "hello world",
            },
        },
        headers={
            "x-rh-identity": "eyJpZGVudGl0eSI6IHsiYWNjb3VudF9udW1iZXIiOiJhY2NvdW50MTIzIiwib3JnX2lkIjoib3JnMTIzIiwidHlwZSI6IlVzZXIiLCJ1c2VyIjp7ImlzX29yZ19hZG1pbiI6dHJ1ZSwgInVzZXJfaWQiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOiJhc3RybyJ9LCJpbnRlcm5hbCI6eyJvcmdfaWQiOiJvcmcxMjMifX19",
        },
    )

    assert raw_response.status == "200 OK"
    json = await raw_response.get_json()

    talk_response = TalkResponse(**json)

    assert talk_response is not None
    assert talk_response.session_id is not None
    assert len(talk_response.response) == 1
    assert talk_response.response[0].type == ResponseType.TEXT
    assert talk_response.response[0].text == "hello world"


async def test_talk_bad_request_invalid_session(test_client) -> None:
    raw_response = await test_client.post(
        "/talk",
        json={
            "session_id": "invalid-session",
            "input": {
                "text": "hello world",
            },
        },
        headers={
            "x-rh-identity": "eyJpZGVudGl0eSI6IHsiYWNjb3VudF9udW1iZXIiOiJhY2NvdW50MTIzIiwib3JnX2lkIjoib3JnMTIzIiwidHlwZSI6IlVzZXIiLCJ1c2VyIjp7ImlzX29yZ19hZG1pbiI6dHJ1ZSwgInVzZXJfaWQiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOiJhc3RybyJ9LCJpbnRlcm5hbCI6eyJvcmdfaWQiOiJvcmcxMjMifX19",
        },
    )

    assert raw_response.status == "400 BAD REQUEST"
    content = await raw_response.get_data()
    assert "invalid-session" in str(content)


async def test_talk_bad_request_invalid_user(test_client) -> None:
    raw_response = await test_client.post(
        "/talk",
        json={
            "session_id": None,
            "input": {
                "text": "hello world",
            },
        },
        headers={
            # org123/1234567890
            "x-rh-identity": "eyJpZGVudGl0eSI6IHsiYWNjb3VudF9udW1iZXIiOiJhY2NvdW50MTIzIiwib3JnX2lkIjoib3JnMTIzIiwidHlwZSI6IlVzZXIiLCJ1c2VyIjp7ImlzX29yZ19hZG1pbiI6dHJ1ZSwgInVzZXJfaWQiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOiJhc3RybyJ9LCJpbnRlcm5hbCI6eyJvcmdfaWQiOiJvcmcxMjMifX19",
        },
    )

    assert raw_response.status == "200 OK"
    json = await raw_response.get_json()
    session_id = json["session_id"]

    raw_response = await test_client.post(
        "/talk",
        json={
            "session_id": session_id,
            "input": {
                "text": "hello world",
            },
        },
        headers={
            # other-org/1234567890
            "x-rh-identity": "eyJpZGVudGl0eSI6IHsiYWNjb3VudF9udW1iZXIiOiJhY2NvdW50MTIzIiwib3JnX2lkIjoib3RoZXItb3JnIiwidHlwZSI6IlVzZXIiLCJ1c2VyIjp7ImlzX29yZ19hZG1pbiI6dHJ1ZSwgInVzZXJfaWQiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOiJhc3RybyJ9LCJpbnRlcm5hbCI6eyJvcmdfaWQiOiJvcmcxMjMifX19",
        },
    )

    assert raw_response.status == "400 BAD REQUEST"
    content = await raw_response.get_data()
    assert "Invalid session" in str(content)


async def test_multiple_requests(test_client) -> None:
    raw_response = await test_client.post(
        "/talk",
        json={
            "session_id": None,
            "input": {
                "text": "hello world",
            },
        },
        headers={
            "x-rh-identity": "eyJpZGVudGl0eSI6IHsiYWNjb3VudF9udW1iZXIiOiJhY2NvdW50MTIzIiwib3JnX2lkIjoib3JnMTIzIiwidHlwZSI6IlVzZXIiLCJ1c2VyIjp7ImlzX29yZ19hZG1pbiI6dHJ1ZSwgInVzZXJfaWQiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOiJhc3RybyJ9LCJpbnRlcm5hbCI6eyJvcmdfaWQiOiJvcmcxMjMifX19",
        },
    )

    assert raw_response.status == "200 OK"
    json = await raw_response.get_json()
    session_id = json["session_id"]

    raw_response = await test_client.post(
        "/talk",
        json={
            "session_id": session_id,
            "input": {
                "text": "hello world again",
            },
        },
        headers={
            "x-rh-identity": "eyJpZGVudGl0eSI6IHsiYWNjb3VudF9udW1iZXIiOiJhY2NvdW50MTIzIiwib3JnX2lkIjoib3JnMTIzIiwidHlwZSI6IlVzZXIiLCJ1c2VyIjp7ImlzX29yZ19hZG1pbiI6dHJ1ZSwgInVzZXJfaWQiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOiJhc3RybyJ9LCJpbnRlcm5hbCI6eyJvcmdfaWQiOiJvcmcxMjMifX19",
        },
    )

    assert raw_response.status == "200 OK"
    json = await raw_response.get_json()
    assert json["session_id"] == session_id
    assert json["response"][0]["type"] == "TEXT"
    assert json["response"][0]["text"] == "hello world again"
