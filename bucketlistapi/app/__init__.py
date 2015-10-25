'''
Initializing the flask app
'''
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from ..config import config


db = SQLAlchemy()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)

    from .api_1 import api_1 as api_1_blueprint
    app.register_blueprint(api_1_blueprint, url_prefix='/api/v1')

    return app
