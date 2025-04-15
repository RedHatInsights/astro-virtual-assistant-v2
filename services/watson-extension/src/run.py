import quart_injector
import common.metrics.quart as quart_metrics
from quart import Quart
import watson_extension.config as config
from common.logging import build_logger

from quart_schema import (
    QuartSchema,
    RequestSchemaValidationError,
    Server,
    ServerVariable,
    Info,
)

from common.types.errors import ValidationError
from watson_extension.quart_schema import WatsonExtensionAPIProvider
from watson_extension.startup import (
    wire_routes,
    injector_from_config,
    injector_defaults,
)

build_logger(config.logger_type)
app = Quart(__name__)
config.log_config()

wire_routes(app)
quart_injector.wire(app, [injector_defaults, injector_from_config])
quart_metrics.register_app(app)
quart_metrics.register_http_metrics(
    app, config.name, lambda r: r.path.startswith("/api")
)


@app.errorhandler(RequestSchemaValidationError)
async def handle_request_validation_error(error):
    return ValidationError(message=str(error.validation_error)), 400


# Must happen after routes, injector, etc
QuartSchema(
    app,
    openapi_path=config.base_url + "/openapi.json",
    openapi_provider_class=WatsonExtensionAPIProvider,
    info=Info(
        title="Virtual assistant watson extension",
        version="2.0.0",
        description="Extension to provide data from the console to virtual assistant",
    ),
    servers=[
        Server(
            url="https://{env}",
            description="Virtual assistant watson extension",
            variables={
                "env": ServerVariable(
                    enum=[
                        "console.redhat.com",
                        "console.stage.redhat.com",
                    ],
                    default="console.redhat.com",
                    description="Available environments",
                )
            },
        ),
        Server(
            url=f"http://127.0.0.1:{config.port}",
            description="Local development server",
        ),
    ],
    security_schemes={
        "service2service": {
            "type": "oauth2",
            "flows": {
                "clientCredentials": {
                    "tokenUrl": "https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token",
                    "scopes": {},
                },
            },
        },
        "service2service-stage": {
            "type": "oauth2",
            "flows": {
                "clientCredentials": {
                    "tokenUrl": "https://sso.stage.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token",
                    "scopes": {},
                }
            },
        },
    },
)

if __name__ == "__main__":
    app.run(port=config.port)
