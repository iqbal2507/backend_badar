from flask import Blueprint
from api.v1_0.auth import auth
from api.v1_0.parameter import parameter
from api.v1_0.controller.menu import menu
from api.v1_0.MenuTeam import MenuTeam
from api.v1_0.MenuKegiatan import MenuKegiatan
from api.v1_0.MenuUser import MenuUser
from api.v1_0.MenuInputan import MenuInputan
from api.v1_0.MenuMonitoring import MenuMonitoring
from api.v1_0.MenuDashboard import MenuDashboard

api_v1_0 = Blueprint('api_v1_0', __name__,url_prefix="/api/v1.0")
api_v1_0.register_blueprint(auth, url_prefix="/")
api_v1_0.register_blueprint(parameter, url_prefix="/parameter")
api_v1_0.register_blueprint(menu, url_prefix="/menu")
api_v1_0.register_blueprint(MenuTeam, url_prefix="/MenuTeam")
api_v1_0.register_blueprint(MenuKegiatan, url_prefix="/MenuKegiatan")
api_v1_0.register_blueprint(MenuUser, url_prefix="/MenuUser")
api_v1_0.register_blueprint(MenuInputan, url_prefix="/MenuInputan")
api_v1_0.register_blueprint(MenuMonitoring, url_prefix="/MenuMonitoring")
api_v1_0.register_blueprint(MenuDashboard, url_prefix="/MenuDashboard")
