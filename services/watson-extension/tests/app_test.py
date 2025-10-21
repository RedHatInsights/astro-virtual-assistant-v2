import json
import os
import sys
import aiohttp

from unittest import mock
import quart_injector

import injector
from aioresponses import aioresponses
from openapi_spec_validator import validate

import pytest

from common.session_storage import Session
from watson_extension.routes.health import StatusResponse, Status
from redis.asyncio import StrictRedis

from pytest_mock_resources import create_redis_fixture, RedisConfig

from common.session_storage.redis import RedisSessionStorage
from . import path_to_resource, get_resource_contents

redis_fixture = create_redis_fixture()

__config_modules = [
    "app_common_python",
    "watson_extension.config",
    "watson_extension.assistant.watson",
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
    return RedisConfig(image="docker.io/valkey/valkey:8.1.4")


@pytest.fixture
def redis(redis_fixture):
    return StrictRedis(**redis_fixture.pmr_credentials.as_redis_kwargs())


@pytest.fixture
def session_storage(redis):
    return RedisSessionStorage(redis)


@pytest.fixture
async def default_app(redis_fixture):
    redis_credentials = redis_fixture.pmr_credentials
    with (
        mock.patch.dict(
            os.environ,
            {
                "CLOWDER_ENABLED": "true",
                "SESSION_STORAGE": "redis",
                "REDIS_HOSTNAME": redis_credentials.host,
                "REDIS_PORT": str(redis_credentials.port),
                "LOGGING_CLOUDWATCH_SECRET_ACCESS_KEY": "test",
                "LOGGING_CLOUDWATCH_ACCESS_KEY_ID": "test",
                "LOGGING_CLOUDWATCH_REGION": "test",
                "LOGGING_CLOUDWATCH_LOG_GROUP": "test",
                "ACG_CONFIG": path_to_resource("app_test/default_clowdapp.json"),
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
    response = await test_client.get(
        "/api/virtual-assistant-watson-extension/v2/openapi.json"
    )
    assert response.status == "200 OK"
    validate(await response.get_json())


async def test_app_health(default_app):
    test_client = default_app.test_client()

    response = await test_client.get(
        "/health/status",
    )

    assert response.status == "200 OK"
    json_response = await response.get_json()
    status_response = StatusResponse(**json_response)

    assert status_response is not None
    assert status_response.status == Status.OK.value


async def test_app_advisor(default_app, aiohttp_mock, session_storage):
    test_client = default_app.test_client()
    await session_storage.put(
        Session(key="1234", user_identity="my-identity", user_id="theorg/theuser")
    )

    aiohttp_mock.get(
        "http://n-api.svc:8000/api/insights/v1/rulecategory/",
        status=200,
        body=json.dumps(
            [{"category": "performance", "id": "123", "name": "performance"}]
        ),
    )

    aiohttp_mock.get(
        "http://n-api.svc:8000/api/insights/v1/rule?impacting=true&rule_status=enabled&category=123&sort=-total_risk&limit=3",
        status=200,
        body=json.dumps(
            {
                "data": [
                    {
                        "rule_id": "rule-1",
                        "description": "smoke testing",
                    },
                    {
                        "rule_id": "rule-2",
                        "description": "more testing",
                    },
                ]
            }
        ),
    )

    response = await test_client.get(
        "/api/virtual-assistant-watson-extension/v2/insights/advisor/recommendations?category=performance",
        headers={"x-rh-session-id": "1234"},
    )

    assert response.status == "200 OK"


async def test_app_advisor_openshift(default_app, aiohttp_mock, session_storage):
    test_client = default_app.test_client()
    await session_storage.put(
        Session(key="1234", user_identity="my-identity", user_id="theorg/theuser")
    )

    aiohttp_mock.get(
        "http://openshift-advisor:8000/api/insights-results-aggregator/v2/clusters",
        status=200,
        body=get_resource_contents("requests/openshift/advisor/clusters.json"),
    )

    response = await test_client.get(
        "/api/virtual-assistant-watson-extension/v2/openshift/advisor/recommendations?category=cluster",
        headers={"x-rh-session-id": "1234"},
    )

    assert response.status == "200 OK"
