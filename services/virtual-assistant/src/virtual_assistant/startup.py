from typing import List

import aiohttp
import injector
from quart import Quart, Blueprint
from redis.asyncio import StrictRedis

from common.session_storage.redis import RedisSessionStorage
from common.session_storage import SessionStorage
from common.session_storage.file import FileSessionStorage

import virtual_assistant.config as config
from virtual_assistant.assistant.response_processor.response_processor import (
    ResponseProcessor,
)
from virtual_assistant.assistant.response_processor.rhel_lightspeed import (
    RhelLightspeed,
)
from virtual_assistant.routes import health
from virtual_assistant.routes import talk
from virtual_assistant.assistant import Assistant
from virtual_assistant.assistant.watson import (
    WatsonAssistant,
    build_assistant,
)
from virtual_assistant.assistant.echo import EchoAssistant


@injector.provider
def redis_session_storage_provider() -> RedisSessionStorage:
    return RedisSessionStorage(
        StrictRedis(
            host=config.redis_hostname,
            port=config.redis_port,
        )
    )


@injector.provider
def console_assistant_watson_provider() -> Assistant:
    return WatsonAssistant(
        assistant=build_assistant(
            config.watson_api_key, config.watson_env_version, config.watson_api_url
        ),
        assistant_id=config.watson_env_id,  # Todo: Should we use a different id for the assistant?
        environment_id=config.watson_env_id,
    )


@injector.provider
def console_assistant_echo_provider() -> Assistant:
    return EchoAssistant()


@injector.provider
def client_session_provider() -> aiohttp.ClientSession:
    return aiohttp.ClientSession()


@injector.multiprovider
def response_processors_rhel_lightspeed_provider(
    session: injector.Inject[aiohttp.ClientSession],
) -> List[ResponseProcessor]:
    return [RhelLightspeed(session, config.rhel_lightspeed_url)]


@injector.multiprovider
def response_processors_empty() -> List[ResponseProcessor]:
    return []


def injector_from_config(binder: injector.Binder) -> None:
    # This gets injected into routes when it is requested.
    # e.g. async def status(session_storage: injector.Inject[SessionStorage]) -> StatusResponse:
    if config.session_storage == "redis":
        binder.bind(
            SessionStorage, to=redis_session_storage_provider, scope=injector.singleton
        )
    elif config.session_storage == "file":
        binder.bind(
            SessionStorage,
            to=FileSessionStorage(".va-session-storage"),
            scope=injector.singleton,
        )

    if config.console_assistant == "echo":
        binder.bind(
            Assistant, to=console_assistant_echo_provider, scope=injector.singleton
        )
    elif config.console_assistant == "watson":
        binder.bind(
            Assistant, to=console_assistant_watson_provider, scope=injector.singleton
        )
    else:
        raise RuntimeError(
            f"Invalid console assistant requested ons startup {config.console_assistant}"
        )

    binder.bind(
        aiohttp.ClientSession, client_session_provider, scope=injector.singleton
    )

    binder.multibind(
        List[ResponseProcessor], response_processors_empty, scope=injector.singleton
    )

    if config.rhel_lightspeed_enabled:
        binder.multibind(
            List[ResponseProcessor],
            response_processors_rhel_lightspeed_provider,
            scope=injector.singleton,
        )


def wire_routes(app: Quart) -> None:
    public_root = Blueprint("public_root", __name__, url_prefix=config.base_url)
    private_root = Blueprint("private_root", __name__)

    # Connecting private routes (/)
    private_root.register_blueprint(health.blueprint)

    # Connect public routes ({config.base_url})
    public_root.register_blueprint(talk.blueprint)

    app.register_blueprint(public_root)
    app.register_blueprint(private_root)
