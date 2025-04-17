import quart_injector
import common.metrics.quart as quart_metrics
from quart import Quart
from quart_schema import (
    QuartSchema,
    RequestSchemaValidationError,
    Info,
    Server,
    ServerVariable,
)
import virtual_assistant.config as config

from common.logging import build_logger
from virtual_assistant.quart_schema import VirtualAssistantOpenAPIProvider
from common.types.errors import ValidationError
from virtual_assistant.startup import wire_routes, injector_from_config

build_logger(config.logger_type)
config.log_config()
app = Quart(__name__)

wire_routes(app)
quart_injector.QuartModule(app)
quart_injector.wire(app, injector_from_config)
quart_metrics.register_app(app)
quart_metrics.register_http_metrics(
    app, config.name, lambda r: r.path.startswith("/api")
)


@app.errorhandler(RequestSchemaValidationError)
async def handle_request_validation_error(error):
    return ValidationError(message=str(error.validation_error)), 400


# Must happen after routes, injector, etc
schema = QuartSchema(
    app,
    openapi_path=config.base_url + "/openapi.json",
    openapi_provider_class=VirtualAssistantOpenAPIProvider,
    info=Info(
        title="Virtual assistant",
        version="2.0.0",
        description="Virtual assistant backend service",
    ),
    servers=[
        Server(
            url="http://{env}",
            description="Virtual assistant hosted services",
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
)

# Add openapi path to our temporal -v2 path
app.add_url_rule("/api/virtual-assistant-v2/v2/openapi.json", "openapi", schema.openapi)

if __name__ == "__main__":
    app.run(port=config.port)
