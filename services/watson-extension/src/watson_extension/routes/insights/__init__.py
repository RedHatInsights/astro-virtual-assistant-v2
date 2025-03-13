from quart import Blueprint
from . import advisor, vulnerability, image_builder

blueprint = Blueprint("insights", __name__, url_prefix="/insights")

blueprint.register_blueprint(advisor.blueprint)
blueprint.register_blueprint(vulnerability.blueprint)
blueprint.register_blueprint(image_builder.blueprint)
