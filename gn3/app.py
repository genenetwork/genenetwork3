"""Entry point from spinning up flask"""
import os
import sys
import logging
import getpass
import traceback

from typing import Dict
from typing import Union

from flask import Flask
from flask_cors import CORS # type: ignore

from gn3.loggers import setup_app_handlers
from gn3.api.gemma import gemma
from gn3.api.rqtl import rqtl
from gn3.api.general import general
from gn3.api.heatmaps import heatmaps
from gn3.api.correlation import correlation
from gn3.api.data_entry import data_entry
from gn3.api.wgcna import wgcna
from gn3.api.ctl import ctl
from gn3.errors import register_error_handlers
from gn3.api.async_commands import async_commands
from gn3.api.menu import menu
from gn3.api.search import search
from gn3.api.metadata import metadata
from gn3.api.sampledata import sampledata
from gn3.api.llm import GnQNA
from gn3.auth import oauth2
from gn3.case_attributes import caseattr


def create_app(config: Union[Dict, str, None] = None) -> Flask:
    """Create a new flask object"""
    app = Flask(__name__)
    # Load default configuration
    app.config.from_object("gn3.settings")

    # Load environment configuration
    if "GN3_CONF" in os.environ:
        app.config.from_envvar('GN3_CONF')

    # Load app specified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith(".py"):
            app.config.from_pyfile(config)

    setup_app_handlers(app)
    # DO NOT log anything before this point
    logging.info("Guix Profile: '%s'.", os.environ.get("GUIX_PROFILE"))
    logging.info("Python Executable: '%s'.", sys.executable)

    CORS(
        app,
        origins=app.config["CORS_ORIGINS"],
        allow_headers=app.config["CORS_HEADERS"],
        supports_credentials=True, intercept_exceptions=False)

    app.register_blueprint(general, url_prefix="/api/")
    app.register_blueprint(gemma, url_prefix="/api/gemma")
    app.register_blueprint(rqtl, url_prefix="/api/rqtl")
    app.register_blueprint(heatmaps, url_prefix="/api/heatmaps")
    app.register_blueprint(correlation, url_prefix="/api/correlation")
    app.register_blueprint(data_entry, url_prefix="/api/dataentry")
    app.register_blueprint(wgcna, url_prefix="/api/wgcna")
    app.register_blueprint(ctl, url_prefix="/api/ctl")
    app.register_blueprint(async_commands, url_prefix="/api/async_commands")
    app.register_blueprint(menu, url_prefix="/api/menu")
    app.register_blueprint(search, url_prefix="/api/search")
    app.register_blueprint(metadata, url_prefix="/api/metadata")
    app.register_blueprint(sampledata, url_prefix="/api/sampledata")
    app.register_blueprint(oauth2, url_prefix="/api/oauth2")
    app.register_blueprint(caseattr, url_prefix="/api/case-attribute")
    app.register_blueprint(GnQNA, url_prefix="/api/llm")

    register_error_handlers(app)
    return app
