"""Entry point from spinning up flask"""

import os
import sys
import logging
from pathlib import Path

from typing import Dict
from typing import Union

from flask import Flask
from flask_cors import CORS  # type: ignore

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
from gn3.api.llm import gnqa
from gn3.api.rqtl2 import rqtl2
from gn3.api.streaming import streaming
from gn3.case_attributes import caseattr
from gn3.api.lmdb_sample_data import lmdb_sample_data


class ConfigurationError(Exception):
    """Raised in case of a configuration error."""


def verify_app_config(app: Flask) -> None:
    """Verify that configuration variables are as expected
    It includes:
        1. making sure mandatory settings are defined
        2. provides examples for what to set as config variables (helps local dev)
    """
    app_config = {
        "AUTH_SERVER_URL": """AUTH_SERVER_URL is used for api requests that need login.
        For local dev, use the running auth server url, which defaults to http://127.0.0.1:8081
        """,
    }
    error_message = []

    for setting, err in app_config.items():
        print(f"{setting}: {app.config.get(setting)}")
        if setting in app.config and bool(app.config[setting]):
            continue
        error_message.append(err)
    if error_message:
        raise ConfigurationError("\n".join(error_message))


def create_app(config: Union[Dict, str, None] = None) -> Flask:
    """Create a new flask object"""
    app = Flask(__name__)
    # Load default configuration
    app.config.from_object("gn3.settings")

    # Load environment configuration
    if "GN3_CONF" in os.environ:
        app.config.from_envvar("GN3_CONF")

    # Load app specified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith(".py"):
            app.config.from_pyfile(config)

    # BEGIN: SECRETS -- Should be the last of the settings to load
    secrets_file = os.environ.get("GN3_SECRETS")
    if secrets_file and Path(secrets_file).exists():
        app.config.from_envvar("GN3_SECRETS")
    # END: SECRETS
    verify_app_config(app)
    setup_app_handlers(app)
    # DO NOT log anything before this point
    logging.info("Guix Profile: '%s'.", os.environ.get("GUIX_PROFILE"))
    logging.info("Python Executable: '%s'.", sys.executable)

    CORS(
        app,
        origins=app.config["CORS_ORIGINS"],
        allow_headers=app.config["CORS_HEADERS"],
        supports_credentials=True,
        intercept_exceptions=False,
    )

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
    app.register_blueprint(caseattr, url_prefix="/api/case-attribute")
    app.register_blueprint(gnqa, url_prefix="/api/llm")
    app.register_blueprint(rqtl2, url_prefix="/api/rqtl2")
    app.register_blueprint(streaming, url_prefix="/api/stream")
    app.register_blueprint(lmdb_sample_data, url_prefix="/api/lmdb")

    register_error_handlers(app)
    return app
