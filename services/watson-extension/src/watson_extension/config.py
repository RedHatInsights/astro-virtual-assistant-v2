from common.config import config, log_config as _log_config
from decouple import Csv, Choices
import logging

name = config("APP_NAME", default="virtual-assistant-watson-extension")
base_url = config("BASE_URL", default="/api/virtual-assistant-watson-extension/v2/")
port = config("PORT", default=5050, cast=int)
environment_name = config("ENVIRONMENT_NAME", default="stage", cast=str)

is_running_locally = config("IS_RUNNING_LOCALLY", default=False, cast=bool)
if is_running_locally:
    __platform_url = config("PLATFORM_URL", default="https://console.redhat.com")
else:
    __platform_url = None

# Urls
advisor_url = config("ENDPOINT__ADVISOR_BACKEND__API__URL", default=__platform_url)

# Platform requests
platform_request = config(
    "PLATFORM_REQUEST",
    default="dev" if is_running_locally else "platform",
    cast=Choices(["dev", "platform"]),
)
if platform_request == "dev":
    dev_platform_request_offline_token = config("DEV_PLATFORM_REQUEST_OFFLINE_TOKEN")
    dev_platform_request_refresh_url = config(
        "DEV_PLATFORM_REQUEST_REFRESH_URL",
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
    redis_username = config("REDIS_USERNAME")
    redis_password = config("REDIS_PASSWORD")


def log_config():
    import sys

    _log_config(sys.modules[__name__], logging.getLogger(__name__).info)
