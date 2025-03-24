from unittest.mock import MagicMock

import pytest
from common.session_storage import SessionStorage, Session
from werkzeug.exceptions import BadRequest

import quart

from .. import async_value

from common.identity import QuartUserIdentityProvider


async def test_quart_user_identity_provider():
    request = MagicMock(quart.Request)
    request.headers = {"x-rh-session-id": "123456"}

    session_storage = MagicMock(SessionStorage)
    session_storage.get = MagicMock(
        return_value=async_value(
            Session(key="123456", user_id="user-id", user_identity="identity")
        )
    )

    testee = QuartUserIdentityProvider(request, session_storage)
    assert await testee.get_user_identity() == "identity"
    session_storage.get.assert_called_once_with("123456")


async def test_quart_user_identity_fails_on_missing_header():
    request = MagicMock(quart.Request)
    request.headers = {"other": "123456"}

    testee = QuartUserIdentityProvider(request, MagicMock())
    with pytest.raises(BadRequest):
        await testee.get_user_identity()
