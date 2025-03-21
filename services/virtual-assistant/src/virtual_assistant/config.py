from decouple import Choices
from common.config import config, log_config as _log_config
import logging

name = config("APP_NAME", default="virtual-assistant")
base_url = config("BASE_URL", default="/api/virtual-assistant/v2/")
port = config("PORT", default=5000, cast=int)
environment_name = config("ENVIRONMENT_NAME", default="stage", cast=str)

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
        "RHEL_LIGHTSPEED_URL"
    )  # This might change once we figure out how the url is provided


def log_config():
    import sys

    _log_config(sys.modules[__name__], logging.getLogger(__name__).info)
