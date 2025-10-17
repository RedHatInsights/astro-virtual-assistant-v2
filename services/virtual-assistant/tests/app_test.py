import os
import sys
import quart_injector
import injector
import aiohttp

from unittest import mock
from unittest.mock import MagicMock
from aioresponses import aioresponses
from openapi_spec_validator import validate

from virtual_assistant.assistant import ResponseType
from virtual_assistant.assistant.response_processor.rhel_lightspeed import (
    RhelLightspeedResponse,
    RhelLightspeedData,
)
from virtual_assistant.routes.talk import TalkResponse
from . import get_json_resource

import pytest
from pytest_mock_resources import create_redis_fixture, RedisConfig

redis_fixture = create_redis_fixture()

__config_modules = [
    "app_common_python",
    "virtual_assistant.config",
    "virtual_assistant.assistant.watson",
    "run",
]


@pytest.fixture(autouse=True)
def clear_app_config():
    for module in __config_modules:
        if module in sys.modules:
            del sys.modules[module]


@pytest.fixture
async def aiohttp_mock():
    with aioresponses() as m:
        yield m


@pytest.fixture(scope="session")
def pmr_redis_config() -> RedisConfig:
    return RedisConfig(image="docker.io/valkey/valkey:7.2.11")


@pytest.fixture
async def assistant_v2():
    create_session_response = MagicMock()
    create_session_response.get_result = MagicMock(
        return_value={"session_id": "session_id_0001"}
    )

    message_response = MagicMock()
    message_response.get_result = MagicMock(
        return_value=get_json_resource("itest_watson_response.json")
    )

    mocked = MagicMock()
    mocked.create_session = MagicMock(return_value=create_session_response)
    mocked.message = MagicMock(return_value=message_response)
    return mocked


@pytest.fixture
async def default_app(redis_fixture, assistant_v2):
    redis_credentials = redis_fixture.pmr_credentials
    with (
        mock.patch("ibm_watson.AssistantV2", MagicMock(return_value=assistant_v2)),
        mock.patch.dict(
            os.environ,
            {
                "CLOWDER_ENABLED": "true",
                "SESSION_STORAGE": "redis",
                "REDIS_HOSTNAME": redis_credentials.host,
                "REDIS_PORT": str(redis_credentials.port),
                "CONSOLE_ASSISTANT": "watson",
                "WATSON_API_URL": "some-url",
                "WATSON_API_KEY": "my-key",
                "WATSON_ENV_ID": "my-env",
                "LOGGING_CLOUDWATCH_SECRET_ACCESS_KEY": "test",
                "LOGGING_CLOUDWATCH_ACCESS_KEY_ID": "test",
                "LOGGING_CLOUDWATCH_REGION": "test",
                "LOGGING_CLOUDWATCH_LOG_GROUP": "test",
                "RHEL_LIGHTSPEED_ENABLED": "true",
                "RHEL_LIGHTSPEED_URL": "rhel-lightspeed",
                "DEBUG": "true",
                "__DOT_ENV_FILE": ".i-dont-exist",
            },
            clear=True,
        ),
    ):
        from run import app

        yield app
        # Close the ClientSession to prevent some warnings
        injector_container = app.extensions["injector"]
        assert injector_container is not None
        session: aiohttp.ClientSession = injector_container.get(aiohttp.ClientSession)
        await session.close()


async def test_app_injection(default_app):
    injector_container = default_app.extensions["injector"]
    assert injector_container is not None

    # Manually inject the RequestScope - since we are not going to do any request
    injector_container.get(quart_injector.RequestScope).push()

    for rule in default_app.url_map.iter_rules():
        if rule.endpoint not in default_app.view_functions:
            continue

        if rule.endpoint == "openapi":
            continue

        route_function = default_app.view_functions.get(rule.endpoint)
        bindings = injector.get_bindings(route_function)

        for param in bindings.values():
            if injector_container.get(param) is None:
                assert injector_container.create_object(param) is not None


async def test_openapi(default_app):
    test_client = default_app.test_client()
    response = await test_client.get("/api/virtual-assistant/v2/openapi.json")
    assert response.status == "200 OK"
    validate(await response.get_json())


async def test_app(default_app, aiohttp_mock):
    test_client = default_app.test_client()
    aiohttp_mock.post(
        "rhel-lightspeed/api/lightspeed/v1/infer",
        status=200,
        body=RhelLightspeedResponse(
            data=RhelLightspeedData(
                model_id="a-model",
                text="42",
            )
        ).model_dump_json(),
    )

    response = await test_client.post(
        "/api/virtual-assistant/v2/talk",
        json={
            "session_id": None,
            "input": {
                "text": "what's the answer to the ultimate question of life, the universe, and everything?",
            },
        },
        headers={
            "x-rh-identity": "eyJpZGVudGl0eSI6IHsiYWNjb3VudF9udW1iZXIiOiJhY2NvdW50MTIzIiwib3JnX2lkIjoib3JnMTIzIiwidHlwZSI6IlVzZXIiLCJ1c2VyIjp7ImlzX29yZ19hZG1pbiI6dHJ1ZSwgInVzZXJfaWQiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOiJhc3RybyJ9LCJpbnRlcm5hbCI6eyJvcmdfaWQiOiJvcmcxMjMifX19",
        },
    )

    assert response.status == "200 OK"
    json = await response.get_json()
    talk_response = TalkResponse(**json)

    assert talk_response is not None
    assert talk_response.session_id == "session_id_0001"
    assert len(talk_response.response) == 3
    assert talk_response.response[0].type == ResponseType.TEXT
    assert talk_response.response[0].text == "hello world"
    assert talk_response.response[1].type == ResponseType.TEXT
    assert talk_response.response[1].text == "42"
    assert talk_response.response[2].type == ResponseType.OPTIONS
    assert talk_response.response[2].text == "Do you want pie?"
    assert len(talk_response.response[2].options) == 2
    assert talk_response.response[2].options[0].text == "Bring it on!"
    assert talk_response.response[2].options[0].value == "yes"
    assert talk_response.response[2].options[1].text == "Eww!"
    assert talk_response.response[2].options[1].value == "no"
