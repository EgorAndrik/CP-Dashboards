import os
from flask import Flask
import flask
from . import default_config
from .errorHandlers import register_errorhandlers
from flask_cors import CORS
from .api import api

import logging

def create_app(config: dict | str | None = None):
    app = Flask(__name__)

    # load default configuration
    app.config.from_object(default_config)

    # load environment configuration
    if 'APP_CONF' in os.environ:
        app.config.from_envvar('APP_CONF')

    # load app specified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif isinstance(config, str):
            app.config.from_pyfile(config)

    app.config.from_prefixed_env()

    setup_app(app)

    return app


def setup_app(app: Flask):
    CORS(app)
    register_errorhandlers(app)

    app.register_blueprint(api)
