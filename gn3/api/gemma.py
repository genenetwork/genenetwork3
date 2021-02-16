"""Endpoints for running the gemma cmd"""
from flask import Blueprint
from flask import jsonify

gemma = Blueprint("gemma", __name__)


@gemma.route("/")
def index() -> str:
    """Test endpoint"""
    return jsonify(result="hello world")


@gemma.route("/version")
def get_version():
    pass


@gemma.route("/k-compute/<token>", methods=["POST"])
def run_k_compute(token) -> str:
    pass


@gemma.route("/lmm/gwa/<token>/<k_file_name>", methods=["POST"])
def run_gwa(token, k_file_name) -> str:
    pass


@gemma.route("/pheno-permutation/<token>", methods=["POST"])
def run_pheno_permutation(token) -> str:
    pass


@gemma.route("/lmm2/loco/<token>", methods=["POST"])
def run_gemma_with_loco(token) -> str:
    pass
