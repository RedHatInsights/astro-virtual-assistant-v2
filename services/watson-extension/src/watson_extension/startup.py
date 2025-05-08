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
    make_client_session_provider,
)
from watson_extension.auth import Authentication
from watson_extension.auth.api_key_authentication import ApiKeyAuthentication
from watson_extension.auth.no_authentication import NoAuthentication
from watson_extension.auth.service_account_authentication import (
    ServiceAccountAuthentication,
)
from watson_extension.clients import (
    AdvisorURL,
    AdvisorOpenshiftURL,
    ChromeServiceURL,
    VulnerabilityURL,
    ContentSourcesURL,
    RhsmURL,
    SourcesURL,
    NotificationsGWURL,
    PlatformNotificationsURL,
)
from watson_extension.clients.insights.advisor import AdvisorClient, AdvisorClientHttp
from watson_extension.clients.openshift.advisor import (
    AdvisorClient as AdvisorOpenshiftClient,
    AdvisorClientHttp as AdvisorOpenshiftClientHttp,
)
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
from watson_extension.clients.platform.chrome import (
    ChromeServiceClient,
    ChromeServiceClientHttp,
)
from watson_extension.clients.platform.sources import (
    SourcesClient,
    SourcesClientHttp,
)
from watson_extension.clients.insights.notifications import (
    NotificationsClient,
    NotificationsClientHttp,
    NotificationClientNoOp,
)
from watson_extension.clients.platform.notifications import (
    PlatformNotificationsClient,
    PlatformNotificationsClientHttp,
)
from watson_extension.clients.platform.integrations import (
    IntegrationsClient,
    IntegrationsClientHttp,
)
from watson_extension.clients.platform.rbac import (
    RbacURL,
    RBACClient,
    RBACClientHttp,
    RBACClientNoOp,
)
from watson_extension.clients.general.redhat_status import (
    RedhatStatusClient,
    RedhatStatusClientHttp,
)


from common.platform_request import (
    AbstractPlatformRequest,
)
from watson_extension.routes import health
from watson_extension.routes import insights
from watson_extension.routes import openshift
from watson_extension.routes import platform
from watson_extension.routes import general

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
                app_name=config.name,
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
                app_name=config.name,
            ),
            scope=injector.singleton,
        )
    elif config.platform_request == "platform":
        binder.bind(
            AbstractPlatformRequest,
            to=make_platform_request_provider(app_name=config.name),
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
        binder.bind(
            NotificationsClient,
            NotificationClientNoOp,
            scope=quart_injector.RequestScope,
        )
        binder.bind(
            RBACClient,
            RBACClientNoOp,
            scope=quart_injector.RequestScope,
        )
    else:
        # This injector is per request - as we should extract the data for each request.
        binder.bind(
            AbstractUserIdentityProvider,
            quart_user_identity_provider,
            scope=quart_injector.RequestScope,
        )
        binder.bind(
            NotificationsClient,
            NotificationsClientHttp,
            scope=quart_injector.RequestScope,
        )
        binder.bind(
            RBACClient,
            RBACClientHttp,
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
    binder.bind(
        AdvisorOpenshiftURL, to=config.advisor_openshift_url, scope=injector.singleton
    )
    binder.bind(
        ChromeServiceURL, to=config.chrome_service_url, scope=injector.singleton
    )
    binder.bind(SourcesURL, to=config.sources_url, scope=injector.singleton)
    binder.bind(
        NotificationsGWURL, to=config.notifications_gw_url, scope=injector.singleton
    )
    binder.bind(
        PlatformNotificationsURL,
        to=config.platform_notifications_url,
        scope=injector.singleton,
    )
    binder.bind(RbacURL, to=config.rbac_url, scope=injector.singleton)


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
    binder.bind(
        AdvisorOpenshiftClient,
        AdvisorOpenshiftClientHttp,
        scope=quart_injector.RequestScope,
    )
    binder.bind(SourcesClient, SourcesClientHttp, scope=quart_injector.RequestScope)
    binder.bind(
        ChromeServiceClient,
        ChromeServiceClientHttp,
    )
    binder.bind(
        PlatformNotificationsClient,
        PlatformNotificationsClientHttp,
        scope=quart_injector.RequestScope,
    )
    binder.bind(
        IntegrationsClient, IntegrationsClientHttp, scope=quart_injector.RequestScope
    )
    binder.bind(
        RedhatStatusClient, RedhatStatusClientHttp, scope=quart_injector.RequestScope
    )


def wire_routes(app: Quart) -> None:
    public_root = Blueprint("public_root", __name__, url_prefix=config.base_url)
    private_root = Blueprint("private_root", __name__)

    # Connecting private routes (/)
    private_root.register_blueprint(health.blueprint)

    # Connect public routes ({config.base_url})
    public_root.register_blueprint(platform.blueprint)
    public_root.register_blueprint(insights.blueprint)
    public_root.register_blueprint(openshift.blueprint)
    public_root.register_blueprint(general.blueprint)

    @public_root.before_request
    async def authentication_check(authentication: injector.Inject[Authentication]):
        await authentication.check_auth(quart.request)

    app.register_blueprint(public_root)
    app.register_blueprint(private_root)
