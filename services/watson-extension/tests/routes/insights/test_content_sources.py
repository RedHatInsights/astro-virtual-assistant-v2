from unittest.mock import MagicMock

import injector
import pytest
from quart.typing import TestClientProtocol

from watson_extension.clients.insights.content_sources import (
    GetPopularRepositoriesResponse,
    RepositoriesBulkCreateResponse,
    ContentSourcesClient,
)
from ..common import app_with_blueprint

from watson_extension.routes.insights.content_sources import blueprint
from ... import async_value


@pytest.fixture
async def content_sources_client() -> MagicMock:
    return MagicMock(ContentSourcesClient)


@pytest.fixture
async def test_client(content_sources_client) -> TestClientProtocol:
    def injector_binder(binder: injector.Binder):
        binder.bind(ContentSourcesClient, content_sources_client)

    return app_with_blueprint(blueprint, injector_binder).test_client()


async def test_custom_repositories_enabled(
    test_client, content_sources_client, snapshot
) -> None:
    content_sources_client.get_popular_repositories = MagicMock(
        return_value=async_value(
            GetPopularRepositoriesResponse(
                data=[
                    {
                        "suggested_name": "EPEL 8 repo",
                        "distribution_arch": "blah",
                        "distribution_versions": ["1"],
                        "gpg_key": "keykeykey",
                        "metadata_verification": True,
                        "url": "example.com",
                    }
                ]
            )
        )
    )

    content_sources_client.repositories_bulk_create = MagicMock(
        return_value=async_value(
            RepositoriesBulkCreateResponse(
                response="enabled",
            )
        )
    )

    response = await test_client.get(
        "/content_sources/enable_custom_repositories?version=EPEL 8",
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == snapshot


async def test_custom_repositories_already_enabled(
    test_client, content_sources_client, snapshot
) -> None:
    content_sources_client.get_popular_repositories = MagicMock(
        return_value=async_value(
            GetPopularRepositoriesResponse(
                data=[
                    {
                        "suggested_name": "EPEL 9 repo",
                        "distribution_arch": "blah",
                        "distribution_versions": ["1"],
                        "gpg_key": "keykeykey",
                        "metadata_verification": True,
                        "url": "example.com",
                    }
                ]
            )
        )
    )

    content_sources_client.repositories_bulk_create = MagicMock(
        return_value=async_value(
            RepositoriesBulkCreateResponse(
                response="already_enabled",
            )
        )
    )

    response = await test_client.get(
        "/content_sources/enable_custom_repositories?version=EPEL 9",
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == snapshot


async def test_custom_repositories_error(
    test_client, content_sources_client, snapshot
) -> None:
    content_sources_client.get_popular_repositories = MagicMock(
        return_value=async_value(
            GetPopularRepositoriesResponse(
                data=[
                    {
                        "suggested_name": "EPEL 8 repo",
                        "distribution_arch": "blah",
                        "distribution_versions": ["1"],
                        "gpg_key": "keykeykey",
                        "metadata_verification": True,
                        "url": "example.com",
                    }
                ]
            )
        )
    )

    content_sources_client.repositories_bulk_create = MagicMock(
        return_value=async_value(RepositoriesBulkCreateResponse(response=None))
    )

    response = await test_client.get(
        "/content_sources/enable_custom_repositories?version=EPEL 8",
    )
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == snapshot
