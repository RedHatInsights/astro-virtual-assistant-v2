from unittest.mock import MagicMock

import injector
import pytest
from quart.typing import TestClientProtocol

from watson_extension.clients.insights.image_builder import (
    EnableCustomRepositoriesResponse,
    ImageBuilderClient,
)
from ..common import app_with_blueprint

from watson_extension.routes.insights.image_builder import blueprint
from ... import async_value, get_test_template


@pytest.fixture
async def image_builder_client() -> MagicMock:
    return MagicMock(ImageBuilderClient)


@pytest.fixture
async def test_client(image_builder_client) -> TestClientProtocol:
    def injector_binder(binder: injector.Binder):
        binder.bind(ImageBuilderClient, image_builder_client)

    return app_with_blueprint(blueprint, injector_binder).test_client()


async def test_custom_repositories_enabled(test_client, image_builder_client) -> None:
    image_builder_client.enable_custom_repositories = MagicMock(
        return_value=async_value(
            EnableCustomRepositoriesResponse(
                response="enabled",
            )
        )
    )

    response = await test_client.get(
        "/image_builder/enable_custom_repositories?version=EPEL 8",
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == get_test_template(
        "insights/image_builder/custom_repositories_enabled.txt"
    )


async def test_custom_repositories_already_enabled(
    test_client, image_builder_client
) -> None:
    image_builder_client.enable_custom_repositories = MagicMock(
        return_value=async_value(
            EnableCustomRepositoriesResponse(
                response="already_enabled",
            )
        )
    )

    response = await test_client.get(
        "/image_builder/enable_custom_repositories?version=EPEL 9",
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == get_test_template(
        "insights/image_builder/custom_repositories_already_enabled.txt"
    )


async def test_custom_repositories_error(test_client, image_builder_client) -> None:
    image_builder_client.enable_custom_repositories = MagicMock(
        return_value=async_value(EnableCustomRepositoriesResponse(response=None))
    )

    response = await test_client.get(
        "/image_builder/enable_custom_repositories?version=EPEL 8",
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == get_test_template(
        "insights/image_builder/custom_repositories_error.txt"
    )
