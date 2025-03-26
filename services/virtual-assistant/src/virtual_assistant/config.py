from decouple import Choices
from common.config import config, log_config as _log_config
import logging


name = config("APP_NAME", default="virtual-assistant")
base_url = config("BASE_URL", default="/api/virtual-assistant/v2/")
port = config("PORT", default=5000, cast=int)
environment_name = config("ENVIRONMENT_NAME", default="stage", cast=str)

is_running_locally = config("IS_RUNNING_LOCALLY", default=False, cast=bool)
if is_running_locally:
    __platform_url = config("PLATFORM_URL", default="https://console.redhat.com")
else:
    __platform_url = None

logger_type = config(
    "LOGGER_TYPE", default="basic", cast=Choices(["basic", "cloudwatch"])
)

console_dot_base_url = config(
    "CONSOLEDOT_BASE_URL", default="https://console.redhat.com"
)

# Session storage
session_storage = config(
    "SESSION_STORAGE", default="file", cast=Choices(["file", "redis"])
)
if session_storage == "redis":
    redis_hostname = config("REDIS_HOSTNAME")
    redis_port = config("REDIS_PORT")


console_assistant = config(
    "CONSOLE_ASSISTANT", default="echo", cast=Choices(["echo", "watson"])
)
if console_assistant == "watson":
    watson_api_url = config("WATSON_API_URL")
    watson_api_key = config("WATSON_API_KEY")
    watson_env_id = config("WATSON_ENV_ID")
    watson_env_version = config(
        "WATSON_ENV_VERSION", default="2024-08-25"
    )  # Needs updating if watson releases breaking change. See: https://cloud.ibm.com/apidocs/assistant-v2?code=python#versioning


rhel_lightspeed_enabled = config("RHEL_LIGHTSPEED_ENABLED", default=False, cast=bool)
if rhel_lightspeed_enabled:
    rhel_lightspeed_url = config(
        "RHEL_LIGHTSPEED_URL", default=__platform_url
    )  # This might change once we figure out how the url is provided

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

proxy = config("HTTPS_PROXY", default=None)


def log_config():
    import sys

    _log_config(sys.modules[__name__], logging.getLogger(__name__).info)
