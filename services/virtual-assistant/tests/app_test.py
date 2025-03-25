import os
import sys

from unittest import mock
from unittest.mock import MagicMock
from aioresponses import aioresponses

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
    return RedisConfig(image="docker.io/redis:5.0.7")


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


async def test_app(assistant_v2, redis_fixture, aiohttp_mock, clear_app_config):
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

        from run import app

        test_client = app.test_client()
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
        assert len(talk_response.response) == 2
        assert talk_response.response[0].type == ResponseType.TEXT
        assert talk_response.response[0].text == "hello world"
        assert talk_response.response[1].type == ResponseType.TEXT
        assert talk_response.response[1].text == "42"
