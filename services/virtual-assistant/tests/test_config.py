import os
from unittest import mock
import sys

from . import path_to_resource
import pytest

__config_modules = [
    "app_common_python",
    "common",
    "virtual_assistant.config",
]


@pytest.fixture(autouse=True)
def clear_app_config():
    loaded_module_keys = [*sys.modules.keys()]
    for module in __config_modules:
        for loaded_module_key in loaded_module_keys:
            if loaded_module_key.startswith(module):
                del sys.modules[loaded_module_key]


@mock.patch.dict(
    os.environ,
    {
        "CLOWDER_ENABLED": "true",
        "SESSION_STORAGE": "redis",
        "ACG_CONFIG": path_to_resource("clowdapp-ephemeral.json"),
        "CONSOLE_ASSISTANT": "watson",
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
