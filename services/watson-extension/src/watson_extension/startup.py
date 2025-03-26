import aiohttp
import injector
import quart
import quart_injector
from quart import Quart, Blueprint

from common.providers import (
    make_redis_session_storage_provider,
    make_file_session_storage_provider,
    make_dev_platform_request_provider,
    make_sa_platform_request_provider,
    make_platform_request_provider,
)
from watson_extension.auth import Authentication
from watson_extension.auth.api_key_authentication import ApiKeyAuthentication
from watson_extension.auth.no_authentication import NoAuthentication
from watson_extension.auth.service_account_authentication import (
    ServiceAccountAuthentication,
)
from watson_extension.clients import (
    AdvisorURL,
    VulnerabilityURL,
    ContentSourcesURL,
    RhsmURL,
)
from watson_extension.clients.aiohttp_session import aiohttp_session
from watson_extension.clients.insights.advisor import AdvisorClient, AdvisorClientHttp
from watson_extension.clients.insights.vulnerability import (
    VulnerabilityClient,
    VulnerabilityClientHttp,
)
from watson_extension.clients.insights.content_sources import (
    ContentSourcesClient,
    ContentSourcesClientHttp,
)
from watson_extension.clients.insights.rhsm import (
    RhsmClient,
    RhsmClientHttp,
)
from common.platform_request import (
    AbstractPlatformRequest,
)
from watson_extension.routes import health
from watson_extension.routes import insights

import watson_extension.config as config

from common.session_storage import SessionStorage
from common.identity import (
    QuartWatsonExtensionUserIdentityProvider,
    AbstractUserIdentityProvider,
    FixedUserIdentityProvider,
)


@injector.provider
def api_key_authentication_provider() -> Authentication:
    return ApiKeyAuthentication(config.api_keys)


@injector.provider
def sa_authentication_provider() -> Authentication:
    return ServiceAccountAuthentication(config.sa_client_id)


@injector.provider
def quart_user_identity_provider(
    session_storage: injector.Inject[SessionStorage],
) -> QuartWatsonExtensionUserIdentityProvider:
    import quart

    return QuartWatsonExtensionUserIdentityProvider(quart.request, session_storage)


def injector_from_config(binder: injector.Binder) -> None:
    # Read configuration and assemble our dependencies
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

    if config.authentication_type == "no-auth":
        binder.bind(Authentication, to=NoAuthentication, scope=injector.singleton)
    elif config.authentication_type == "api-key":
        binder.bind(
            Authentication, to=api_key_authentication_provider, scope=injector.singleton
        )
    elif config.authentication_type == "service-account":
        binder.bind(
            Authentication, to=sa_authentication_provider, scope=injector.singleton
        )
    else:
        raise RuntimeError(
            f"Unexpected authentication type {config.authentication_type}"
        )

    # urls
    binder.bind(AdvisorURL, to=config.advisor_url, scope=injector.singleton)
    binder.bind(VulnerabilityURL, to=config.vulnerability_url, scope=injector.singleton)
    binder.bind(
        ContentSourcesURL, to=config.content_sources_url, scope=injector.singleton
    )
    binder.bind(RhsmURL, to=config.rhsm_url, scope=injector.singleton)


def injector_defaults(binder: injector.Binder) -> None:
    # clients
    binder.bind(AdvisorClient, AdvisorClientHttp, scope=quart_injector.RequestScope)
    binder.bind(
        VulnerabilityClient, VulnerabilityClientHttp, scope=quart_injector.RequestScope
    )
    binder.bind(
        ContentSourcesClient,
        ContentSourcesClientHttp,
        scope=quart_injector.RequestScope,
    )
    binder.bind(RhsmClient, RhsmClientHttp, scope=quart_injector.RequestScope)

    # aiohttp session
    binder.bind(aiohttp.ClientSession, aiohttp_session, scope=injector.singleton)


def wire_routes(app: Quart) -> None:
    public_root = Blueprint("public_root", __name__, url_prefix=config.base_url)
    private_root = Blueprint("private_root", __name__)

    # Connecting private routes (/)
    private_root.register_blueprint(health.blueprint)

    # Connect public routes ({config.base_url})
    public_root.register_blueprint(insights.blueprint)

    @public_root.before_request
    async def authentication_check(authentication: injector.Inject[Authentication]):
        await authentication.check_auth(quart.request)

    app.register_blueprint(public_root)
    app.register_blueprint(private_root)
