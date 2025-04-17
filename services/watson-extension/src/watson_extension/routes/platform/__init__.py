from quart import Blueprint
from . import chrome, notifications

blueprint = Blueprint("platform", __name__, url_prefix="/platform")

blueprint.register_blueprint(chrome.blueprint)
blueprint.register_blueprint(notifications.blueprint)
