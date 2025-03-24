from typing import List

import aiohttp
import injector
import quart_injector
from quart import Quart, Blueprint
from redis.asyncio import StrictRedis

from common.identity import (
    QuartUserIdentityProvider,
    AbstractUserIdentityProvider,
    FixedUserIdentityProvider,
)
from common.platform_request import (
    AbstractPlatformRequest,
    DevPlatformRequest,
    PlatformRequest,
    ServiceAccountPlatformRequest,
)
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
def dev_platform_request(
    session: injector.Inject[aiohttp.ClientSession],
) -> DevPlatformRequest:
    return DevPlatformRequest(
        session,
        refresh_token=config.dev_platform_request_offline_token,
        refresh_token_url=config.dev_platform_request_refresh_url,
    )


@injector.provider
def sa_platform_request(
    session: injector.Inject[aiohttp.ClientSession],
) -> ServiceAccountPlatformRequest:
    return ServiceAccountPlatformRequest(
        session,
        token_url=config.sa_platform_request_token_url,
        sa_id=config.sa_platform_request_id,
        sa_secret=config.sa_platform_request_secret,
    )


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
    if config.proxy:
        return aiohttp.ClientSession(proxy=f"http://{config.proxy}")

    return aiohttp.ClientSession()


@injector.multiprovider
def response_processors_rhel_lightspeed_provider(
    platform_request: injector.Inject[AbstractPlatformRequest],
    user_identity_provider: injector.Inject[AbstractUserIdentityProvider],
) -> List[ResponseProcessor]:
    return [
        RhelLightspeed(
            config.rhel_lightspeed_url, user_identity_provider, platform_request
        )
    ]


@injector.multiprovider
def response_processors_empty() -> List[ResponseProcessor]:
    return []


@injector.provider
async def quart_user_identity_provider(
    session_storage: injector.Inject[SessionStorage],
) -> QuartUserIdentityProvider:
    import quart

    return QuartUserIdentityProvider(quart.request, session_storage)


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

    if config.is_running_locally:
        binder.bind(
            AbstractUserIdentityProvider,
            FixedUserIdentityProvider,
            scope=injector.singleton,
        )
    else:
        # This injector is per request - as we should extract the data for each request.
        binder.bind(
            AbstractUserIdentityProvider,
            quart_user_identity_provider,
            scope=quart_injector.RequestScope,
        )

    binder.bind(
        aiohttp.ClientSession, client_session_provider, scope=injector.singleton
    )

    if config.platform_request == "dev":
        binder.bind(
            AbstractPlatformRequest, to=dev_platform_request, scope=injector.singleton
        )
    elif config.platform_request == "sa":
        binder.bind(
            AbstractPlatformRequest, to=sa_platform_request, scope=injector.singleton
        )
    else:
        binder.bind(
            AbstractPlatformRequest, to=PlatformRequest, scope=injector.singleton
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
    public_root_original = Blueprint(
        "public_root_original", __name__, url_prefix=config.base_url
    )
    public_root_alias = Blueprint(
        "public_root_alias", __name__, url_prefix="/api/virtual-assistant-v2/v2/"
    )

    public_root = Blueprint("public_root", __name__)
    private_root = Blueprint("private_root", __name__)

    public_root_original.register_blueprint(public_root)
    public_root_alias.register_blueprint(public_root)

    # Connecting private routes (/)
    private_root.register_blueprint(health.blueprint)

    # Connect public routes ({config.base_url})
    public_root.register_blueprint(talk.blueprint)

    app.register_blueprint(public_root_original)
    app.register_blueprint(public_root_alias)
    app.register_blueprint(private_root)
