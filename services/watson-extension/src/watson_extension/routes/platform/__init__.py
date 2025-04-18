from quart import Blueprint
from . import chrome

blueprint = Blueprint("platform", __name__, url_prefix="/platform")

blueprint.register_blueprint(chrome.blueprint)
