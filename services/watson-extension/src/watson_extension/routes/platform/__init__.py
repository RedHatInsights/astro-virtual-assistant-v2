from quart import Blueprint
from . import chrome, rbac, notifications, integrations

blueprint = Blueprint("platform", __name__, url_prefix="/platform")

blueprint.register_blueprint(chrome.blueprint)
blueprint.register_blueprint(notifications.blueprint)
blueprint.register_blueprint(integrations.blueprint)
blueprint.register_blueprint(rbac.blueprint)
