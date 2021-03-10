"""Entry point from spinning up flask"""
import os

from typing import Dict
from typing import Union
from flask import Flask
from gn3.config import get_config
from gn3.api.gemma import gemma
from gn3.api.general import general
from gn3.api.correlation import correlation


def create_app(config: Union[Dict, str, None] = None) -> Flask:
    """Create a new flask object"""
    app = Flask(__name__)
    # Load default configuration
    app.config.from_object("gn3.settings")

    my_config = get_config()

    app.config.from_object(my_config["dev"])

    # Load environment configuration
    if "GN3_CONF" in os.environ:
        app.config.from_envvar('GN3_CONF')

    # Load app specified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith(".py"):
            app.config.from_pyfile(config)
    app.register_blueprint(general, url_prefix="/api/")
    app.register_blueprint(gemma, url_prefix="/api/gemma")
    app.register_blueprint(correlation,url_prefix="/api/correlation")

    return app
