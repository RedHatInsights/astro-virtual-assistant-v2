import aiohttp
import pytest
from aioresponses import aioresponses

from virtual_assistant.assistant import (
    Query,
    ResponseCommand,
    ResponseText,
    ResponseType,
)
from virtual_assistant.assistant.response_processor.rhel_lightspeed import (
    RhelLightspeed,
    RhelLightspeedResponse,
    RhelLightspeedData,
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


@pytest.fixture
async def rhel_lightspeed(session):
    return RhelLightspeed(session, "")


async def test_rhel_lightspeed(rhel_lightspeed, aiohttp_mock):
    aiohttp_mock.post(
        "/infer",
        status=200,
        body=RhelLightspeedResponse(
            data=RhelLightspeedData(
                model_id="a-model",
                model_version="1.0.0",
                created_at="2025-03-20T20:05:40Z",
                generated_token_count=300,
                input_token_count=200,
                stop_reason="idk",
                text="42",
                prompt="the Ultimate Question of Life, the Universe, and Everything.",
            )
        ).model_dump_json(),
    )

    processed = await rhel_lightspeed.process(
        [ResponseCommand(command="lightspeed", args=["rhel"])],
        Query(text="how are you?"),
    )

    assert len(processed) == 1
    assert processed[0].type == ResponseType.TEXT
    assert processed[0].text == "42"
    aiohttp_mock.assert_called_once()


async def test_rhel_lightspeed_ignores_others(rhel_lightspeed, aiohttp_mock):
    aiohttp_mock.post(
        "/infer",
        status=200,
        body=RhelLightspeedResponse(
            data=RhelLightspeedData(
                model_id="a-model",
                model_version="1.0.0",
                created_at="2025-03-20T20:05:40Z",
                generated_token_count=300,
                input_token_count=200,
                stop_reason="idk",
                text="42",
                prompt="the Ultimate Question of Life, the Universe, and Everything.",
            )
        ).model_dump_json(),
    )

    processed = await rhel_lightspeed.process(
        [
            ResponseText(
                text="Hello world",
            ),
            ResponseCommand(command="lightspeed", args=["rhel"]),
            ResponseText(text="more"),
            ResponseCommand(command="something-else", args=["rhel"]),
            ResponseCommand(command="lightspeed", args=["ansible"]),
        ],
        Query(text="how are you?"),
    )

    assert len(processed) == 5
    assert processed[0].type == ResponseType.TEXT
    assert processed[2].type == ResponseType.TEXT
    assert processed[3].type == ResponseType.COMMAND
    assert processed[4].type == ResponseType.COMMAND

    assert processed[1].type == ResponseType.TEXT
    assert processed[1].text == "42"
    aiohttp_mock.assert_called_once()


async def test_rhel_lightspeed_not_called_without_command(
    rhel_lightspeed, aiohttp_mock
):
    processed = await rhel_lightspeed.process(
        [
            ResponseText(
                text="Hello world",
            ),
            ResponseText(text="more"),
            ResponseCommand(command="something-else", args=["rhel"]),
            ResponseCommand(command="lightspeed", args=["ansible"]),
        ],
        Query(text="how are you?"),
    )

    assert len(processed) == 4
    assert processed[0].type == ResponseType.TEXT
    assert processed[1].type == ResponseType.TEXT
    assert processed[2].type == ResponseType.COMMAND
    assert processed[3].type == ResponseType.COMMAND

    aiohttp_mock.assert_not_called()
