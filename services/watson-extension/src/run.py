import common.metrics.quart as quart_metrics
import quart_injector
import watson_extension.config as config
from common.logging import build_logger
from common.security_log import log_shutdown, log_startup, security_log
from common.types.errors import ValidationError
from quart import Quart, request
from quart_schema import (
    Info,
    QuartSchema,
    RequestSchemaValidationError,
    Server,
    ServerVariable,
)
from watson_extension.quart_schema import WatsonExtensionAPIProvider
from watson_extension.startup import (
    injector_defaults,
    injector_from_config,
    wire_routes,
)

build_logger(config.logger_type)
app = Quart(__name__)
config.log_config()

wire_routes(app)


@app.before_serving
async def startup():
    log_startup(config.name)


@app.after_serving
async def shutdown():
    log_shutdown(config.name)


quart_injector.QuartModule(app)
quart_injector.wire(app, [injector_defaults, injector_from_config])
quart_metrics.register_app(app, config.metrics_port)
quart_metrics.register_http_metrics(
    app, config.name, lambda r: r.path.startswith("/api")
)


@app.errorhandler(RequestSchemaValidationError)
async def handle_request_validation_error(error):
    return ValidationError(message=str(error.validation_error)), 400


@app.errorhandler(500)
async def handle_internal_error(error):
    actual_error = getattr(error, "original_exception", error)
    security_log(
        action="ERROR",
        resource_type="request",
        resource_id=request.path,
        outcome="failure",
        principal={"type": "system"},
        reason=str(actual_error),
        service=config.name,
    )
    return {"message": "Internal server error"}, 500


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
