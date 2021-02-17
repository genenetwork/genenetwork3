"""Endpoints for running the gemma cmd"""
from flask import Blueprint
from flask import current_app
from flask import jsonify

from gn3.commands import run_cmd

gemma = Blueprint("gemma", __name__)


@gemma.route("/version")
def get_version():
    """Display the installed version of gemma-wrapper"""
    gemma_cmd = current_app.config['APP_DEFAULTS'].get('GEMMA_WRAPPER_CMD')
    return jsonify(
        run_cmd(f"{gemma_cmd} -v | head -n 1"))







