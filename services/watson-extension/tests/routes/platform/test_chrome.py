from unittest.mock import MagicMock

import injector
import pytest
from quart.typing import TestClientProtocol

from watson_extension.clients.platform.chrome import (
    ChromeServiceClient,
    Favorite,
    User,
)
from ..common import app_with_blueprint

from watson_extension.routes.platform.chrome import blueprint
from ... import async_value, get_test_template


@pytest.fixture
async def chrome_client() -> MagicMock:
    chrome_client = MagicMock(ChromeServiceClient)
    chrome_client.modify_favorite_service = MagicMock(
        return_value=async_value([
            Favorite(id="asdfg", pathname="/insights/foo", favorite=True, user_identity_id="1234"),
            Favorite(id="asdfg", pathname="/insights/bar", favorite=False, user_identity_id="1234")
        ])
    )

    chrome_client.get_user = MagicMock(
        return_value=async_value(
            User(
                account_id="1234",
                first_login=False,
                day_one=False,
                last_login="2023-01-01",
                last_visited_pages=[],
                favorite_pages=[
                    Favorite(id="bar2", pathname="/insights/bar2", favorite=True, user_identity_id="1234")
                ],
                visited_bundles={},
            )
        )
    )

    chrome_client.get_generated_services = MagicMock(
        return_value=async_value([{
            "description": "foo",
            "id": "str",
            "links": [{
                "title": "barGroup",
                "isGroup": True, 
                "href": "/insights/bar",
                "group": "insights",
                "id": "barGroup",
                "links": [
                    {
                        "appId": "bar1",
                        "description": "barring this test from passing",
                        "filterable": False,
                        "href": "/insights/bar1/run-damnit",
                        "icon": "AITechnologyIcon",
                        "id": "bar1",
                        "title": "bar1"
                    },
                    {
                        "appId": "bar2",
                        "description": "barring this test from passing",
                        "filterable": False,
                        "href": "/insights/bar2/run-damnit",
                        "icon": "AITechnologyIcon",
                        "id": "bar2",
                        "isExternal": True,
                        "title": "bar2"
                    },
                    {
                        "appId": "bar3",
                        "description": "barring this test from passing",
                        "filterable": False,
                        "href": "/insights/bar2/run-damnit",
                        "icon": "AITechnologyIcon",
                        "id": "bar3",
                        "title": "bar3"
                    },
                ]
            }],
            "title": "foo",
            "href": "/insights/foo",
            "group": "insights",
        }])
    )
    return chrome_client


@pytest.fixture
async def test_client(chrome_client) -> TestClientProtocol:
    def injector_binder(binder: injector.Binder):
        binder.bind(ChromeServiceClient, chrome_client)

    return app_with_blueprint(blueprint, injector_binder).test_client()


async def test_favoriting_add_favorite(test_client, chrome_client) -> None:
    response = await test_client.post(
        "/chrome/favorites", query_string={"favoriting": True, "title": "bar1"}
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == get_test_template("platform/chrome/add_favorite.txt")


async def test_favoriting_external_service(test_client, chrome_client) -> None:
    response = await test_client.post(
        "/chrome/favorites", query_string={"favoriting": True, "title": "bar2"}
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == get_test_template("platform/chrome/external_service.txt")


async def test_favoriting_already_favorited(test_client, chrome_client) -> None:
    response = await test_client.post(
        "/chrome/favorites", query_string={"favoriting": True, "title": "bar3"}
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == get_test_template("platform/chrome/already_favorited.txt")


async def test_favoriting_not_found(test_client, chrome_client) -> None:
    response = await test_client.post(
        "/chrome/favorites", query_string={"favoriting": True, "title": "not-found"}
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == get_test_template("platform/chrome/not_found_favorite.txt")
