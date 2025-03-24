from quart import Blueprint
from . import advisor, inventory, vulnerability, content_sources, rhsm

blueprint = Blueprint("insights", __name__, url_prefix="/insights")

blueprint.register_blueprint(advisor.blueprint)
blueprint.register_blueprint(inventory.blueprint)
blueprint.register_blueprint(vulnerability.blueprint)
blueprint.register_blueprint(content_sources.blueprint)
blueprint.register_blueprint(rhsm.blueprint)
