import os

from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from gn3.computations.rqtl import generate_rqtl_cmd
from gn3.computations.gemma import do_paths_exist

rqtl = Blueprint("rqtl", __name__)

@rqtl.route("/compute", methods=["POST"])
def compute():
    working_dir = os.path.join(current_app.config.get("TMPDIR"))

    genofile = request.form['geno_file']
    phenofile = request.form['pheno_file']

    if not do_paths_exist([genofile, phenofile]):
        raise FileNotFoundError

    kwarg_list = ["addcovar", "model", "method", "interval", "nperm", "scale", "control_marker"]

    rqtl_kwargs = {"geno": genofile, "pheno": phenofile}
    for kwarg in kwarg_list:
        if kwarg in request.form:
            rqtl_kwargs[kwarg] = request.form[kwarg]

    results = generate_rqtl_cmd(
        rqtl_wrapper_cmd = current_app.config.get("RQTL_WRAPPER_CMD"),
        output_dir = current_app.config.get('TMPDIR'),
        rqtl_wrapper_kwargs = rqtl_kwargs
    )

    return jsonify(results)

