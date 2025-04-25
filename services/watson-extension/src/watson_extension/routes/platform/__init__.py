from quart import Blueprint
from . import chrome, notifications, integrations

blueprint = Blueprint("platform", __name__, url_prefix="/platform")

blueprint.register_blueprint(chrome.blueprint)
blueprint.register_blueprint(notifications.blueprint)
blueprint.register_blueprint(integrations.blueprint)
