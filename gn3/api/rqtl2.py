""" File contains endpoints for rqlt2"""
import shutil
from pathlib import Path
from flask import current_app
from flask import jsonify
from flask import Blueprint
from flask import request
from gn3.computations.rqtl2 import (compose_rqtl2_cmd,
                                    prepare_files,
                                    validate_required_keys,
                                    write_input_file,
                                    process_qtl2_results
                                    )
from gn3.computations.streaming import run_process
from gn3.computations.streaming import enable_streaming

rqtl2 = Blueprint("rqtl2", __name__)


@rqtl2.route("/compute", methods=["POST"])
@enable_streaming
def compute(log_file):
    """Endpoint for computing QTL analysis using R/QTL2"""
    data = request.json
    required_keys = ["crosstype", "geno_data","pheno_data", "geno_codes"]
    valid, error = validate_required_keys(required_keys,data)
    if not valid:
        return jsonify(error=error), 400
    # Provide atleast one  of this data entries.
    if "physical_map_data" not in data and "geno_map_data" not in data:
        return jsonify(error="You need to Provide\
        Either the Physical map or Geno Map data of markers"), 400
    run_id = request.args.get("id", "output")
    # prepare necessary files and dir for computation
    (workspace_dir, input_file,
     output_file, _log2_file) = prepare_files(current_app.config.get("TMPDIR"))
    # write the input file with data required for creating the cross
    write_input_file(input_file, workspace_dir, data)
    # TODO : Implement a better way for fetching the file Path.
    rqtl_path =Path(__file__).absolute().parent.parent.parent.joinpath("scripts/rqtl2_wrapper.R")
    if not rqtl_path.is_file():
        return jsonify({"error" : f"The script {rqtl_path} does not exists"}), 400
    rqtl2_cmd = compose_rqtl2_cmd(rqtl_path, input_file,
                                  output_file, workspace_dir,
                                  data, current_app.config)
    process_output = run_process(rqtl2_cmd.split(),log_file, run_id)
    if process_output["code"] != 0:
        # Err out for any non-zero status code
        return jsonify(process_output), 400
    results = process_qtl2_results(output_file)
    shutil.rmtree(workspace_dir, ignore_errors=True, onerror=None)
    return jsonify(results)
