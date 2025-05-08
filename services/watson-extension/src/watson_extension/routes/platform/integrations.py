import enum
import injector
from pydantic import BaseModel
from typing import Optional, List

from quart import Blueprint, render_template
from quart_schema import validate_response, validate_querystring, document_headers

from watson_extension.core.platform.integrations import (
    IntegrationType as CoreIntegrationType,
    IntegrationsCore,
)
from watson_extension.clients.platform import IntegrationInfo
from watson_extension.routes import RHSessionIdHeader


blueprint = Blueprint("integrations", __name__, url_prefix="/integrations")


class RedhatIntegrationsValidateNameRequestQuery(BaseModel):
    integrations_setup_name: str


class RedhatIntegrationsValidateNameResponse(BaseModel):
    integration_name_valid: bool


class RedhatIntegrationsSetupRequestQuery(BaseModel):
    integrations_setup_name: str
    redhat_cluster_identifier: str


class RedhatIntegrationsSetupResponse(BaseModel):
    response: str


class IntegrationTypes(enum.Enum):
    """
    The types of integrations: communications/reporting/webhook
    """

    COMMUNICATIONS = "communications"
    REPORTING = "reporting"
    WEBHOOK = "webhook"


class IntegrationsSetupRequestQuery(BaseModel):
    integration_type: IntegrationTypes
    setup_name: str
    setup_url: str
    setup_secret: str
    setup_use_secret: bool
    setup_type: Optional[str] = None


class IntegrationsSetupResponse(BaseModel):
    response: str


class FetchIntegrationsRequestQuery(BaseModel):
    integration_search_query: Optional[str] = None
    integration_enabled: Optional[bool] = None


class FetchIntegrationsResponse(BaseModel):
    has_errors: bool
    integrations: Optional[List[IntegrationInfo]]


class IntegrationActionTypes(enum.Enum):
    """
    The types of integration actions: resume/pause/delete
    """

    RESUME = "resume"
    PAUSE = "pause"
    DELETE = "delete"


class IntegrationActionsRequestQuery(BaseModel):
    action_type: IntegrationActionTypes
    integration_type: CoreIntegrationType
    integration_id: str


class IntegrationActionsResponse(BaseModel):
    response: str


class IntegrationUpdateTypes(enum.Enum):
    """
    The type of integration info being updated: name/url/secret
    """

    NAME = "name"
    URL = "url"
    SECRET = "secret"


class IntegrationUpdateRequestQuery(BaseModel):
    update_type: IntegrationUpdateTypes
    integration_type: CoreIntegrationType
    integration_id: str
    new_value: str


class IntegrationUpdateResponse(BaseModel):
    response: str


@blueprint.get("/redhat/check_name_valid")
@validate_querystring(RedhatIntegrationsValidateNameRequestQuery)
@validate_response(RedhatIntegrationsValidateNameResponse)
@document_headers(RHSessionIdHeader)
async def redhat_integrations_name_valid(
    query_args: RedhatIntegrationsValidateNameRequestQuery,
    integrations_service: injector.Inject[IntegrationsCore],
) -> RedhatIntegrationsValidateNameResponse:
    return RedhatIntegrationsValidateNameResponse(
        integration_name_valid=await integrations_service.redhat_integrations_validate_name(
            query_args.integrations_setup_name
        )
    )


@blueprint.post("/redhat/setup")
@validate_querystring(RedhatIntegrationsSetupRequestQuery)
@validate_response(RedhatIntegrationsSetupResponse)
@document_headers(RHSessionIdHeader)
async def redhat_integrations_setup(
    query_args: RedhatIntegrationsSetupRequestQuery,
    integrations_service: injector.Inject[IntegrationsCore],
) -> RedhatIntegrationsSetupResponse:
    integration_setup_success = await integrations_service.redhat_integrations_setup(
        query_args.integrations_setup_name, query_args.redhat_cluster_identifier
    )

    if integration_setup_success:
        return RedhatIntegrationsSetupResponse(
            response=await render_template(
                "platform/integrations/redhat_integrations_setup_success.txt.jinja",
            )
        )

    return RedhatIntegrationsSetupResponse(
        response=await render_template(
            "platform/integrations/integrations_setup_error.txt.jinja",
        )
    )


@blueprint.post("/setup")
@validate_querystring(IntegrationsSetupRequestQuery)
@validate_response(IntegrationsSetupResponse)
@document_headers(RHSessionIdHeader)
async def integrations_setup(
    query_args: IntegrationsSetupRequestQuery,
    integrations_service: injector.Inject[IntegrationsCore],
) -> IntegrationsSetupResponse:
    if query_args.integration_type == IntegrationTypes.COMMUNICATIONS:
        if await integrations_service.communications_integrations_setup(
            setup_name=query_args.setup_name,
            setup_url=query_args.setup_url,
            setup_secret=query_args.setup_secret,
            setup_use_secret=query_args.setup_use_secret,
            setup_type=query_args.setup_type,
        ):
            return IntegrationsSetupResponse(
                response=await render_template(
                    "platform/integrations/communications_integrations_setup_success.txt.jinja",
                    integration_setup_type=query_args.setup_type,
                )
            )

    if query_args.integration_type == IntegrationTypes.REPORTING:
        if await integrations_service.reporting_integrations_setup(
            setup_name=query_args.setup_name,
            setup_url=query_args.setup_url,
            setup_secret=query_args.setup_secret,
            setup_use_secret=query_args.setup_use_secret,
            setup_type=query_args.setup_type,
        ):
            return IntegrationsSetupResponse(
                response=await render_template(
                    "platform/integrations/reporting_integrations_setup_success.txt.jinja",
                    integration_setup_type=query_args.setup_type,
                )
            )

    if query_args.integration_type == IntegrationTypes.WEBHOOK:
        if await integrations_service.webhook_integrations_setup(
            setup_name=query_args.setup_name,
            setup_url=query_args.setup_url,
            setup_secret=query_args.setup_secret,
            setup_use_secret=query_args.setup_use_secret,
        ):
            return IntegrationsSetupResponse(
                response=await render_template(
                    "platform/integrations/webhook_integrations_setup_success.txt.jinja",
                )
            )

    return IntegrationsSetupResponse(
        response=await render_template(
            "platform/integrations/integrations_setup_error.txt.jinja",
        )
    )


@blueprint.get("/options")
@validate_querystring(FetchIntegrationsRequestQuery)
@validate_response(FetchIntegrationsResponse)
@document_headers(RHSessionIdHeader)
async def fetch_integrations_options(
    query_args: FetchIntegrationsRequestQuery,
    integrations_service: injector.Inject[IntegrationsCore],
) -> FetchIntegrationsResponse:
    has_errors, integrations = await integrations_service.fetch_integrations(
        integration_search=query_args.integration_search_query,
        integration_enabled=query_args.integration_enabled,
    )

    return FetchIntegrationsResponse(has_errors=has_errors, integrations=integrations)


@blueprint.post("/actions")
@validate_querystring(IntegrationActionsRequestQuery)
@validate_response(IntegrationActionsResponse)
@document_headers(RHSessionIdHeader)
async def integration_actions(
    query_args: IntegrationActionsRequestQuery,
    integrations_service: injector.Inject[IntegrationsCore],
) -> IntegrationActionsResponse:
    if query_args.action_type == IntegrationActionTypes.RESUME:
        if await integrations_service.integration_enable(
            integration_type=query_args.integration_type,
            integration_id=query_args.integration_id,
        ):
            return IntegrationActionsResponse(
                response=await render_template(
                    "platform/integrations/integration_action_resume_success.txt.jinja",
                )
            )

    if query_args.action_type == IntegrationActionTypes.PAUSE:
        if await integrations_service.integration_disable(
            integration_type=query_args.integration_type,
            integration_id=query_args.integration_id,
        ):
            return IntegrationActionsResponse(
                response=await render_template(
                    "platform/integrations/integration_action_pause_success.txt.jinja",
                )
            )

    if query_args.action_type == IntegrationActionTypes.DELETE:
        if await integrations_service.integration_delete(
            integration_type=query_args.integration_type,
            integration_id=query_args.integration_id,
        ):
            return IntegrationActionsResponse(
                response=await render_template(
                    "platform/integrations/integration_action_delete_success.txt.jinja",
                )
            )

    return IntegrationActionsResponse(
        response=await render_template(
            "platform/integrations/integration_edit_error.txt.jinja",
        )
    )


@blueprint.post("/update")
@validate_querystring(IntegrationUpdateRequestQuery)
@validate_response(IntegrationUpdateResponse)
@document_headers(RHSessionIdHeader)
async def integration_update(
    query_args: IntegrationUpdateRequestQuery,
    integrations_service: injector.Inject[IntegrationsCore],
) -> IntegrationUpdateResponse:
    if query_args.update_type == IntegrationUpdateTypes.NAME:
        if await integrations_service.integration_update_name(
            integration_type=query_args.integration_type,
            integration_id=query_args.integration_id,
            new_integration_name=query_args.new_value,
        ):
            return IntegrationUpdateResponse(
                response=await render_template(
                    "platform/integrations/integration_update_name_success.txt.jinja",
                    new_name=query_args.new_value,
                )
            )

    if query_args.update_type == IntegrationUpdateTypes.URL:
        if await integrations_service.integration_update_url(
            integration_type=query_args.integration_type,
            integration_id=query_args.integration_id,
            new_integration_url=query_args.new_value,
        ):
            return IntegrationUpdateResponse(
                response=await render_template(
                    "platform/integrations/integration_update_url_success.txt.jinja",
                    new_url=query_args.new_value,
                )
            )

    if query_args.update_type == IntegrationUpdateTypes.SECRET:
        if await integrations_service.integration_update_secret(
            integration_type=query_args.integration_type,
            integration_id=query_args.integration_id,
            new_integration_secret=query_args.new_value,
        ):
            return IntegrationUpdateResponse(
                response=await render_template(
                    "platform/integrations/integration_update_secret_success.txt.jinja",
                )
            )

    return IntegrationUpdateResponse(
        response=await render_template(
            "platform/integrations/integration_edit_error.txt.jinja",
        )
    )
