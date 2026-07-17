from quart import Blueprint

from . import chrome, integrations, notifications, rbac

blueprint = Blueprint("platform", __name__, url_prefix="/platform")

blueprint.register_blueprint(chrome.blueprint)
blueprint.register_blueprint(notifications.blueprint)
blueprint.register_blueprint(integrations.blueprint)
blueprint.register_blueprint(rbac.blueprint)
