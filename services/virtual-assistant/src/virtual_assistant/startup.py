from typing import List

import aiohttp
import injector
import quart_injector
from quart import Quart, Blueprint


from common.identity import (
    AbstractUserIdentityProvider,
    FixedUserIdentityProvider,
    QuartRedHatUserIdentityProvider,
)
from common.platform_request import (
    AbstractPlatformRequest,
)
from common.session_storage import SessionStorage

import virtual_assistant.config as config
from common.providers import (
    make_dev_platform_request_provider,
    make_sa_platform_request_provider,
    make_platform_request_provider,
    make_client_session_provider,
    make_redis_session_storage_provider,
    make_file_session_storage_provider,
)
from virtual_assistant.assistant.response_processor.combine_empty import CombineEmpty
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
def response_processors_default() -> List[ResponseProcessor]:
    return [CombineEmpty()]


@injector.provider
def quart_user_identity_provider() -> QuartRedHatUserIdentityProvider:
    import quart

    return QuartRedHatUserIdentityProvider(quart.request)


def injector_from_config(binder: injector.Binder) -> None:
    # This gets injected into routes when it is requested.
    # e.g. async def status(session_storage: injector.Inject[SessionStorage]) -> StatusResponse:
    if config.session_storage == "redis":
        binder.bind(
            SessionStorage,
            to=make_redis_session_storage_provider(
                hostname=config.redis_hostname,
                port=config.redis_port,
            ),
            scope=injector.singleton,
        )
    elif config.session_storage == "file":
        binder.bind(
            SessionStorage,
            to=make_file_session_storage_provider(".va-session-storage"),
            scope=injector.singleton,
        )

    binder.bind(
        aiohttp.ClientSession,
        make_client_session_provider(config.proxy),
        scope=injector.singleton,
    )

    if config.platform_request == "dev":
        binder.bind(
            AbstractPlatformRequest,
            to=make_dev_platform_request_provider(
                refresh_token=config.dev_platform_request_offline_token,
                refresh_token_url=config.dev_platform_request_refresh_url,
            ),
            scope=injector.singleton,
        )
    elif config.platform_request == "sa":
        binder.bind(
            AbstractPlatformRequest,
            to=make_sa_platform_request_provider(
                token_url=config.sa_platform_request_token_url,
                sa_id=config.sa_platform_request_id,
                sa_secret=config.sa_platform_request_secret,
            ),
            scope=injector.singleton,
        )
    elif config.platform_request == "platform":
        binder.bind(
            AbstractPlatformRequest,
            to=make_platform_request_provider(),
            scope=injector.singleton,
        )
    else:
        raise RuntimeError(
            f"Unexpected platform request configuration: {config.platform_request}"
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

    if config.console_assistant == "echo":
        binder.bind(
            Assistant, to=console_assistant_echo_provider, scope=injector.singleton
        )
    elif config.console_assistant == "watson":
        binder.bind(
            Assistant,
            to=console_assistant_watson_provider,
            scope=quart_injector.RequestScope,
        )
    else:
        raise RuntimeError(
            f"Invalid console assistant requested ons startup {config.console_assistant}"
        )

    binder.multibind(
        List[ResponseProcessor], response_processors_default, scope=injector.singleton
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
