from common.config import config, log_config as _log_config
from decouple import Csv, Choices
import logging

name = config("APP_NAME", default="virtual-assistant-watson-extension")
base_url = config("BASE_URL", default="/api/virtual-assistant-watson-extension/v2/")
port = config("PORT", default=5050, cast=int)
environment_name = config("ENVIRONMENT_NAME", default="stage", cast=str)

metrics_port = config("METRICS_PORT", default=0, cast=int)

is_running_locally = config("IS_RUNNING_LOCALLY", default=False, cast=bool)
if is_running_locally:
    __platform_url = config("PLATFORM_URL", default="https://console.redhat.com")
else:
    __platform_url = None

# Urls
advisor_url = config("ENDPOINT__ADVISOR_BACKEND__API__URL", default=__platform_url)
rhsm_url = config("ENDPOINT__RHSM_API_PROXY__SERVICE__URL", default=__platform_url)
vulnerability_url = config(
    "ENDPOINT__VULNERABILITY_ENGINE__MANAGER_SERVICE__URL", default=__platform_url
)
content_sources_url = config(
    "ENDPOINT__CONTENT_SOURCES_BACKEND__SERVICE__URL", default=__platform_url
)
advisor_openshift_url = config(
    "ENDPOINT__CCX_SMART_PROXY__SERVICE__URL", default=__platform_url
)
chrome_service_url = config(
    "ENDPOINT__CHROME_SERVICE__API__URL", default=__platform_url
)
sources_url = config("ENDPOINT__SOURCES_API__SVC__URL", default=__platform_url)
notifications_gw_url = config(
    "ENDPOINT__NOTIFICATIONS_GW__SERVICE__URL", default=__platform_url
)
platform_notifications_url = config(
    "ENDPOINT__NOTIFICATIONS_BACKEND__SERVICE__URL", default=__platform_url
)
rbac_url = config("ENDPOINT__RBAC__SERVICE__URL", default=__platform_url)

# Platform requests
platform_request = config(
    "PLATFORM_REQUEST",
    default="dev" if is_running_locally else "platform",
    cast=Choices(["dev", "sa", "platform"]),
)
if platform_request == "dev":
    dev_platform_request_offline_token = config("DEV_PLATFORM_REQUEST_OFFLINE_TOKEN")
    dev_platform_request_refresh_url = config(
        "DEV_PLATFORM_REQUEST_REFRESH_URL",
        default="https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token",
    )
elif platform_request == "sa":
    sa_platform_request_id = config("SA_PLATFORM_REQUEST_ID")
    sa_platform_request_secret = config("SA_PLATFORM_REQUEST_SECRET")
    sa_platform_request_token_url = config(
        "SA_PLATFORM_REQUEST_TOKEN_URL",
        default="https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token",
    )

logger_type = config(
    "LOGGER_TYPE", default="basic", cast=Choices(["basic", "cloudwatch"])
)

authentication_type = config(
    "AUTHENTICATION_TYPE",
    default="no-auth",
    cast=Choices(["no-auth", "api-key", "service-account"]),
)
if authentication_type == "api-key":
    api_keys = config("API_KEYS", default=None, cast=Csv(str))
elif authentication_type == "service-account":
    sa_client_id = config("SA_CLIENT_ID")

# Session storage
session_storage = config(
    "SESSION_STORAGE", default="file", cast=Choices(["file", "redis"])
)
if session_storage == "redis":
    redis_hostname = config("REDIS_HOSTNAME")
    redis_port = config("REDIS_PORT")

proxy = config("HTTPS_PROXY", default=None)


def log_config():
    import sys

    _log_config(sys.modules[__name__], logging.getLogger(__name__).info)
