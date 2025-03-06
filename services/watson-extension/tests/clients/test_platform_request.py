import json

import aiohttp
from typing import Optional
from unittest.mock import MagicMock
from werkzeug.exceptions import InternalServerError

import yarl
from aioresponses import aioresponses
import pytest
import jwt

from watson_extension.clients.platform_request import (
    AbstractPlatformRequest,
    DevPlatformRequest,
)


@pytest.fixture
async def aiohttp_mock():
    with aioresponses() as m:
        yield m


@pytest.fixture
async def session():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


async def test_abstract_platform_request():
    class TestAbstractPlatformRequest(AbstractPlatformRequest):
        def __init__(self, session_mock: MagicMock):
            super().__init__()
            self.session_mock = session_mock

        async def request(
            self,
            method: str,
            base_url: str,
            api_path: str,
            user_identity: Optional[str] = None,
            **kwargs,
        ):
            self.session_mock.request(
                method, base_url, api_path, user_identity, **kwargs
            )

    mock = MagicMock()
    testee = TestAbstractPlatformRequest(mock)

    await testee.get("stuff", "path", "foobar", fwd=True)
    mock.request.assert_called_with("GET", "stuff", "path", "foobar", fwd=True)
    mock.reset_mock()

    await testee.options("stuff", "path", "foobar", fwd=True)
    mock.request.assert_called_with("OPTIONS", "stuff", "path", "foobar", fwd=True)

    await testee.head("stuff", "path", "foobar", fwd=True)
    mock.request.assert_called_with("HEAD", "stuff", "path", "foobar", fwd=True)

    await testee.post("stuff", "path", "foobar", fwd=True)
    mock.request.assert_called_with("POST", "stuff", "path", "foobar", fwd=True)

    await testee.put("stuff", "path", "foobar", fwd=True)
    mock.request.assert_called_with("PUT", "stuff", "path", "foobar", fwd=True)

    await testee.patch("stuff", "path", "foobar", fwd=True)
    mock.request.assert_called_with("PATCH", "stuff", "path", "foobar", fwd=True)

    await testee.delete("stuff", "path", "foobar", fwd=True)
    mock.request.assert_called_with("DELETE", "stuff", "path", "foobar", fwd=True)


async def test_dev_platform_request(session, aiohttp_mock):
    testee = DevPlatformRequest(session, "token", "token-url")

    token = jwt.encode({"value": "yes"}, "stuff")
    aiohttp_mock.post("token-url", status=200, body=json.dumps({"access_token": token}))
    aiohttp_mock.get(
        "target-url/path",
        status=200,
    )

    # Initial call
    resp = await testee.request(
        "GET", "target-url", "/path", user_identity="not-used-but-must-be-present"
    )
    assert resp.status == 200
    aiohttp_mock.assert_called_with(
        "token-url",
        "POST",
        data={
            "grant_type": "refresh_token",
            "client_id": "rhsm-api",
            "refresh_token": "token",
        },
    )
    aiohttp_mock.assert_called_with(
        "target-url/path", "GET", headers={"Authorization": "Bearer " + token}
    )

    # Calling with a token already present
    aiohttp_mock.get(
        "other-url/path",
        status=200,
    )
    resp = await testee.request("GET", "other-url", "/path")
    assert resp.status == 200
    assert len(aiohttp_mock.requests[("POST", yarl.URL("token-url"))]) == 1
    aiohttp_mock.assert_called_with("other-url/path", "GET", headers={})


async def test_dev_platform_request_refresh_if_expired(session, aiohttp_mock):
    testee = DevPlatformRequest(session, "token", "token-url")
    token = jwt.encode({"value": "yes"}, "stuff")

    aiohttp_mock.post("token-url", status=200, body=json.dumps({"access_token": token}))
    aiohttp_mock.get(
        "other-url/path",
        status=200,
    )

    testee._dev_token = "Invalid token"
    resp = await testee.request("GET", "other-url", "/path")
    assert resp.status == 200
    assert len(aiohttp_mock.requests[("POST", yarl.URL("token-url"))]) == 1


async def test_dev_platform_request_fails_to_get_token(session, aiohttp_mock):
    testee = DevPlatformRequest(session, "token", "token-url")

    # Throws if fails to get a token
    with pytest.raises(InternalServerError):
        testee._dev_token = "Invalid token"
        aiohttp_mock.post("token-url", status=500)
        await testee.request("GET", "other-url", "/path")


async def test_dev_platform_request_gets_invalid_token(session, aiohttp_mock):
    testee = DevPlatformRequest(session, "token", "token-url")

    # Also fails if we get an invalid token
    with pytest.raises(Exception):
        testee._dev_token = "Invalid token"
        aiohttp_mock.post(
            "token-url", status=200, body=json.dumps({"access_token": "im not a token"})
        )
        await testee.request("GET", "other-url", "/path")
