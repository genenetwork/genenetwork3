"""Endpoints for running the gemma cmd"""
import os
import redis

from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from gn3.commands import queue_cmd
from gn3.commands import run_cmd
from gn3.computations.gemma import generate_hash_of_string
from gn3.computations.gemma import generate_pheno_txt_file
from gn3.computations.gemma import generate_gemma_computation_cmd

gemma = Blueprint("gemma", __name__)


@gemma.route("/version")
def get_version():
    """Display the installed version of gemma-wrapper"""
    gemma_cmd = current_app.config['APP_DEFAULTS'].get('GEMMA_WRAPPER_CMD')
    return jsonify(
        run_cmd(f"{gemma_cmd} -v | head -n 1"))


# This is basically extracted from genenetwork2
# wqflask/wqflask/marker_regression/gemma_ampping.py
@gemma.route("/k-gwa-computation", methods=["POST"])
def run_gemma():
    """Generates a command for generating K-Values and then later, generate a GWA
command that contains markers. These commands are queued; and the expected
file output is returned.

    """
    data = request.get_json()
    app_defaults = current_app.config.get('APP_DEFAULTS')
    __hash = generate_hash_of_string("".join(data.get("values")))
    gemma_kwargs = {
        "geno_filename": os.path.join(app_defaults.get("GENODIR"), "bimbam",
                                      f"{data.get('genofile_name')}.txt"),
        "trait_filename": generate_pheno_txt_file(
            tmpdir=app_defaults.get("TMPDIR"),
            values=data.get("values"),
            # Generate this file on the fly!
            trait_filename=(f"{data.get('dataset_groupname')}_"
                            f"{data.get('trait_name')}_"
                            f"{__hash}.txt"))}
    k_computation_cmd = generate_gemma_computation_cmd(
        gemma_cmd=app_defaults.get("GEMMA_WRAPPER_CMD"),
        gemma_kwargs=gemma_kwargs,
        output_file=(f"{app_defaults.get('TMPDIR')}/gn2/"
                     f"{data.get('dataset_name')}_K_"
                     f"{__hash}.json"))
    if data.get("covariates"):
        gemma_kwargs["c"] = os.path.join(app_defaults.get("GENODIR"),
                                         "bimbam",
                                         data.get("covariates"))
    gemma_kwargs["lmm"] = data.get("lmm", 9)
    gwa_cmd = generate_gemma_computation_cmd(
        gemma_cmd=app_defaults.get("GEMMA_WRAPPER_CMD"),
        gemma_kwargs=gemma_kwargs,
        output_file=(f"{data.get('dataset_name')}_GWA_"
                     f"{__hash}.txt"))
    if not all([k_computation_cmd, gwa_cmd]):
        return jsonify(status=128,
                       error="Unable to generate cmds for computation!"), 500
    return jsonify(
        unique_id=queue_cmd(conn=redis.Redis(),
                            email=data.get("email"),
                            job_queue=app_defaults.get("REDIS_JOB_QUEUE"),
                            cmd=f"{k_computation_cmd} && {gwa_cmd}"),
        status="queued",
        output_file=(f"{data.get('dataset_name')}_GWA_"
                     f"{__hash}.txt"))
