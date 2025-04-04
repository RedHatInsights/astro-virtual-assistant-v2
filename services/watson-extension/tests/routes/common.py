from typing import Optional, Callable

from quart import Quart, Blueprint
from quart_schema import QuartSchema
import quart_injector
import injector

from watson_extension.clients import AdvisorURL
from common.identity import (
    FixedUserIdentityProvider,
    AbstractUserIdentityProvider,
)


def app_with_blueprint(
    blueprint: Blueprint,
    injector_module: Optional[Callable[[injector.Binder], None]] = None,
) -> Quart:
    app = Quart(__name__, template_folder="../../src/templates")
    app.register_blueprint(blueprint)

    injector_binders = (
        [_injector_config, injector_module]
        if injector_module is not None
        else [_injector_config]
    )

    quart_injector.wire(app, injector_binders)

    QuartSchema(app)  # Ensures we can return objects from the endpoints
    return app


def _injector_config(binder: injector.Binder) -> None:
    binder.bind(AbstractUserIdentityProvider, FixedUserIdentityProvider)

    # URLs
    binder.bind(AdvisorURL, "http://127.0.0.1")
