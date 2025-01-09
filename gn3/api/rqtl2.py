""" File contains endpoints for rqlt2"""

import subprocess
import os
from flask import current_app
from flask import jsonify
from flask import Blueprint
from flask import request

rqtl2 = Blueprint("rqtl2", __name__)


@rqtl2.route("/compute", methods=["GET"])
def compute():
    """Endpoint for computing QTL analysis using R/QTL2"""
    # get the run id to act as file identifier default to output
    run_id = request.args.get("id", "output")
    output_file = os.path.join(current_app.config.get("TMPDIR"),
                               f"{run_id}.txt")
    # this should be computed locally not via files
    rscript_cmd = (
        "Rscript ./scripts/rqtl2_wrapper.R "
        "-i /home/kabui/r_playground/meta_grav.json "
        "-d /home/kabui/r_playground "
        "-o /home/kabui/r_playground/rqtl_output.json "
        "--nperm 100  --threshold 1 --cores 0"
    )
    # pylint: disable=consider-using-with
    process = subprocess.Popen(
        rscript_cmd, shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    for line in iter(process.stdout.readline, b""):
        # these allow endpoint stream to read the file since
        # no read and write file same tiem
        with open(output_file, "a+", encoding="utf-8") as file_handler:
            file_handler.write(line.decode("utf-8"))
    process.stdout.close()
    process.wait()
    if process.returncode == 0:
        return jsonify({"msg": "success",
                        "results": "file_here",
                        "run_id": run_id})
    return jsonify({"msg": "fail",
                    "error": "Process failed",
                    "run_id": run_id})
