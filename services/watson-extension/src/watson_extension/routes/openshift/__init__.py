from quart import Blueprint
from . import advisor

blueprint = Blueprint("openshift", __name__, url_prefix="/openshift")

blueprint.register_blueprint(advisor.blueprint)
