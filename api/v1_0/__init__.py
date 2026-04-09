from flask import Blueprint
from api.v1_0.auth import auth
from api.v1_0.parameter import parameter
from api.v1_0.controller.menu import menu

api_v1_0 = Blueprint('api_v1_0', __name__,url_prefix="/api/v1.0")
api_v1_0.register_blueprint(auth, url_prefix="/")
api_v1_0.register_blueprint(parameter, url_prefix="/parameter")
api_v1_0.register_blueprint(menu, url_prefix="/menu")