"""Endpoints for running the rqtl cmd"""
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from gn3.computations.rqtl import generate_rqtl_cmd
from gn3.computations.gemma import do_paths_exist

rqtl = Blueprint("rqtl", __name__)

@rqtl.route("/compute", methods=["POST"])
def compute():
    """Given at least a geno_file and pheno_file, generate and
run the rqtl_wrapper script and return the results as JSON

    """
    genofile = request.form['geno_file']
    phenofile = request.form['pheno_file']

    if not do_paths_exist([genofile, phenofile]):
        raise FileNotFoundError

    # Split kwargs by those with values and boolean ones that just convert to True/False
    kwargs = ["model", "method", "nperm", "scale", "control_marker"]
    boolean_kwargs = ["addcovar", "interval"]
    all_kwargs = kwargs + boolean_kwargs

    rqtl_kwargs = {"geno": genofile, "pheno": phenofile}
    rqtl_bool_kwargs = []
    for kwarg in all_kwargs:
        if kwarg in request.form:
            if kwarg in kwargs:
                rqtl_kwargs[kwarg] = request.form[kwarg]
            if kwarg in boolean_kwargs:
                rqtl_bool_kwargs.append(kwarg)

    results = generate_rqtl_cmd(
        rqtl_wrapper_cmd=current_app.config.get("RQTL_WRAPPER_CMD"),
        rqtl_wrapper_kwargs=rqtl_kwargs,
        rqtl_wrapper_bool_kwargs=boolean_kwargs
    )

    return jsonify(results)
