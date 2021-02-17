"""Endpoints for running the gemma cmd"""
import os
import redis

from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from gn3.commands import compose_gemma_cmd
from gn3.commands import queue_cmd
from gn3.commands import run_cmd
from gn3.file_utils import jsonfile_to_dict

gemma = Blueprint("gemma", __name__)


@gemma.route("/version")
def get_version():
    """Display the installed version of gemma-wrapper"""
    gemma_cmd = current_app.config['APP_DEFAULTS'].get('GEMMA_WRAPPER_CMD')
    return jsonify(
        run_cmd(f"{gemma_cmd} -v | head -n 1"))


# This is basically extracted from genenetwork2
# wqflask/wqflask/marker_regression/gemma_ampping.py
@gemma.route("/run", methods=["POST"])
def run_gemma():
    """Generates a command for generating K-Values and then later, generate a GWA
command that contains markers. These commands are queued; and the expected
file output is returned.

    """
    data = request.get_json()
    if not data.get("token"):
        return jsonify(status=128, error="Please provide a token"), 400
    app_defaults = current_app.config.get('APP_DEFAULTS')
    metadata = os.path.join(app_defaults.get("TMPDIR"),
                            data.get("token"),
                            data.get("metadata", "metadata.json"))
    if not os.path.isfile(metadata):
        return jsonify(status=128,
                       error=f"{metadata}: file does not exist"), 500
    metadata = jsonfile_to_dict(metadata)
    gemma_kwargs = {
        "g": os.path.join(app_defaults.get("GENODIR"), "bimbam",
                          metadata.get("genotype_file")),
        "p": os.path.join(app_defaults.get("GENODIR"), "bimbam",
                          metadata.get("phenotype_file")),
        "a": os.path.join(app_defaults.get("GENODIR"), "bimbam",
                          metadata.get("snp_file"))}
    generate_k_cmd = compose_gemma_cmd(
        gemma_wrapper_cmd=app_defaults.get("GEMMA_WRAPPER_CMD"),
        gemma_kwargs=gemma_kwargs,
        gemma_args=["-gk", ">",
                    os.path.join(app_defaults.get("TMPDIR"), "gn2",
                                 f"k_output_{data.get('token')}.txt")])
    if metadata.get("covariates"):
        gemma_kwargs["c"] = os.path.join(app_defaults.get("GENODIR"),
                                         "bimbam",
                                         metadata.get("covariates"))
    # Prevents command injection!
    for _, value in gemma_kwargs.items():
        if not os.path.isfile(value):
            return jsonify(status=128, error=f"{value}: Does not exist!"), 500

    gemma_kwargs["lmm"] = 9
    gwa_cmd = compose_gemma_cmd(
        gemma_wrapper_cmd=app_defaults.get("GEMMA_WRAPPER_CMD"),
        gemma_kwargs=gemma_kwargs,
        gemma_args=[">",
                    os.path.join(app_defaults.get("TMPDIR"),
                                 "gn2",
                                 f"gemma_output_{data.get('token')}.txt")])
    unique_id = queue_cmd(conn=redis.Redis(), email=metadata.get("email"),
                          cmd=f"{generate_k_cmd} && {gwa_cmd}")
    return jsonify(unique_id=unique_id, status="queued",
                   output_file=f"gemma_output_{data.get('token')}.txt")
