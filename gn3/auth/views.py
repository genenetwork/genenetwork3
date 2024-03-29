"""The Auth(oris|entic)ation routes/views"""
from flask import Blueprint

from .authorisation.data.views import data
from .authorisation.users.views import users
from .authorisation.roles.views import roles
from .authorisation.groups.views import groups
from .authorisation.resources.views import resources

oauth2 = Blueprint("oauth2", __name__)

oauth2.register_blueprint(data, url_prefix="/data")
oauth2.register_blueprint(users, url_prefix="/user")
oauth2.register_blueprint(roles, url_prefix="/role")
oauth2.register_blueprint(groups, url_prefix="/group")
oauth2.register_blueprint(resources, url_prefix="/resource")
