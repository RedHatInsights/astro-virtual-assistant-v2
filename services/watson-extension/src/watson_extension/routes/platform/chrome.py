from typing import List
import injector
from pydantic import BaseModel

from quart import Blueprint, render_template
from quart_schema import validate_response, validate_querystring, document_headers

from watson_extension.core.platform.chrome import (
    ChromeServiceCore,
)
from watson_extension.routes import RHSessionIdHeader

blueprint = Blueprint("chrome", __name__, url_prefix="/chrome")


class FavoritesRequestQuery(BaseModel):
    title: str
    favoriting: bool  # true is adding a favorite


class FavoritesResponse(BaseModel):
    response: str


class FavoritesOptionsResponseItem(BaseModel):
    title: str
    href: str


class FavoritesOptionsResponse(BaseModel):
    response: List[FavoritesOptionsResponseItem]


@blueprint.post("/favorites")
@validate_querystring(FavoritesRequestQuery)
@validate_response(FavoritesResponse)
@document_headers(RHSessionIdHeader)
async def favorites(
    query_args: FavoritesRequestQuery,
    chrome_service: injector.Inject[ChromeServiceCore],
) -> FavoritesResponse:
    service_data = await chrome_service.get_service_data(
        title=query_args.title,
    )
    if not service_data:
        return FavoritesResponse(
            response=await render_template(
                "platform/chrome/service_not_found.txt.jinja",
                title=query_args.title,
            )
        )
    if service_data["already"] != query_args.favoriting:
        try:
            await chrome_service.modify_favorite_service(
                service_data["href"], favorite=query_args.favoriting
            )
        except Exception:
            return FavoritesResponse(
                response=await render_template(
                    "platform/chrome/request_error.txt.jinja",
                    **service_data,
                )
            )

    if query_args.favoriting:
        return FavoritesResponse(
            response=await render_template(
                "platform/chrome/add_favorite.txt.jinja",
                **service_data,
            )
        )
    else:
        return FavoritesResponse(
            response=await render_template(
                "platform/chrome/delete_favorite.txt.jinja",
                **service_data,
            )
        )


@blueprint.get("/favorites/options")
@validate_response(FavoritesOptionsResponse)
@document_headers(RHSessionIdHeader)
async def favorte_options(
    chrome_service: injector.Inject[ChromeServiceCore],
) -> FavoritesOptionsResponse:
    options = await chrome_service.get_favorite_options()
    return FavoritesOptionsResponse(response=options)
