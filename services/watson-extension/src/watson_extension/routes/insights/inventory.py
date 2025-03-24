import injector
from pydantic import BaseModel

from quart import Blueprint, render_template
from quart_schema import validate_response, validate_querystring, document_headers

from watson_extension.core.insights.inventory import (
    InventoryCore,
)
from watson_extension.routes import RHSessionIdHeader

blueprint = Blueprint("inventory", __name__, url_prefix="/inventory")


class ActivationKeysRequestQuery(BaseModel):
    name: str


class ActivationKeysResponse(BaseModel):
    response: str


@blueprint.post("/activation-key")
@validate_querystring(ActivationKeysRequestQuery)
@validate_response(ActivationKeysResponse)
@document_headers(RHSessionIdHeader)
async def activation_keys(
    query_args: ActivationKeysRequestQuery,
    inventory_service: injector.Inject[InventoryCore],
) -> ActivationKeysResponse:
    activation_key_response_response = await inventory_service.create_activation_keys(query_args.name)

    return ActivationKeysResponse(
        response=await render_template(
            "insights/inventory/create_activation_keys.txt.jinja",
            response=activation_key_response_response,
            name=query_args.name,
        )
    )
