"""Endpoints for running the rqtl cmd"""
import os

from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from gn3.computations.rqtl import generate_rqtl_cmd, process_rqtl_output, process_perm_output
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
    boolean_kwargs = ["addcovar", "interval", "pstrata"]
    all_kwargs = kwargs + boolean_kwargs

    rqtl_kwargs = {"geno": genofile, "pheno": phenofile}
    rqtl_bool_kwargs = []
    for kwarg in all_kwargs:
        if kwarg in request.form:
            if kwarg in kwargs:
                rqtl_kwargs[kwarg] = request.form[kwarg]
            if kwarg in boolean_kwargs:
                rqtl_bool_kwargs.append(kwarg)

    rqtl_cmd = generate_rqtl_cmd(
        rqtl_wrapper_cmd=current_app.config.get("RQTL_WRAPPER_CMD"),
        rqtl_wrapper_kwargs=rqtl_kwargs,
        rqtl_wrapper_bool_kwargs=rqtl_bool_kwargs
    )

    rqtl_output = {}
    if not os.path.isfile(os.path.join(current_app.config.get("TMPDIR"),
                                       "output", rqtl_cmd.get('output_file'))):
        os.system(rqtl_cmd.get('rqtl_cmd'))

    rqtl_output['results'] = process_rqtl_output(rqtl_cmd.get('output_file'))

    rqtl_output['results'] = process_rqtl_output(rqtl_cmd.get('output_file'))
    if int(rqtl_kwargs['nperm']) > 0:
        rqtl_output['perm_results'], rqtl_output['suggestive'], rqtl_output['significant'] = \
        process_perm_output(rqtl_cmd.get('output_file'))

    return jsonify(rqtl_output)
