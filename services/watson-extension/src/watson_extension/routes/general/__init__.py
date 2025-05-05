from quart import Blueprint
from . import redhat_status

blueprint = Blueprint("general", __name__, url_prefix="/general")

blueprint.register_blueprint(redhat_status.blueprint)
