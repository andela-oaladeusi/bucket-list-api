from flask import Blueprint

# creating blueprint for api_1 app
api_1 = Blueprint('api_1', __name__)

from . import views, errors, authentication
