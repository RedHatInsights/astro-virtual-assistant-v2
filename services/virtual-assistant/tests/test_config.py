import os
from unittest import mock
import sys

from . import path_to_resource
import pytest

__config_modules = [
    "app_common_python",
    "virtual_assistant.config",
]


@pytest.fixture(autouse=True)
def clear_app_config():
    for module in __config_modules:
        if module in sys.modules:
            del sys.modules[module]


@mock.patch.dict(
    os.environ,
    {
        "CLOWDER_ENABLED": "true",
        "SESSION_STORAGE": "redis",
        "ACG_CONFIG": path_to_resource("clowdapp-ephemeral.json"),
        "WATSON_API_URL": "some-url",
        "WATSON_API_KEY": "my-key",
        "WATSON_ENV_ID": "my-env",
        "__DOT_ENV_FILE": ".i-dont-exist",
    },
    clear=True,
)
def test_clowdapp_public_endpoints():
    import virtual_assistant.config as config

    assert config.session_storage == "redis"
    assert config.redis_hostname == "virtual-assistant-v2-redis.ephemeral-inqgsu.svc"
    assert config.redis_port == 6379
    assert config.watson_api_url == "some-url"
    assert config.watson_api_key == "my-key"
    assert config.watson_env_id == "my-env"
