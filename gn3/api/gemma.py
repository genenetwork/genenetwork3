"""Endpoints for running the gemma cmd"""
from flask import Blueprint
from flask import current_app
from flask import jsonify

gemma = Blueprint("gemma", __name__)

from gn3.commands import run_cmd

@gemma.route("/")
def index() -> str:
    """Test endpoint"""
    return jsonify(result="hello world")


@gemma.route("/version")
def get_version():
    """Display the installed version of gemma-wrapper"""
    gemma_cmd = current_app.config['APP_DEFAULTS'].get('GEMMA_WRAPPER_CMD')
    return jsonify(
        run_cmd(f"{gemma_cmd} -v | head -n 1"))

@gemma.route("/k-compute/<token>", methods=["POST"])
def run_k_compute(token) -> str:
    pass


@gemma.route("/lmm/gwa/<token>/<k_file_name>", methods=["POST"])
def run_gwa(token, k_file_name) -> str:
    pass


@gemma.route("/pheno-permutation/<token>", methods=["POST"])
def run_pheno_permutation(token) -> str:
    pass


