""" File contains endpoints for rqlt2"""

import subprocess
import uuid
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
        f"Rscript ./scripts/rqtl2_wrapper.R "
        f"-i /home/kabui/r_playground/meta_grav.json "
        f"-d /home/kabui/r_playground "
        f"-o /home/kabui/r_playground/rqtl_output.json "
        f"--nperm 100  --threshold 1 --cores 0"
    )
    process = subprocess.Popen(
        rscript_cmd, shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    for line in iter(process.stdout.readline, b""):
        # these allow endpoint stream to read the file since
        # no read and write file same tiem
        with open(output_file, "a+") as file_handler:
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


@rqtl2.route("/stream/<identifier>",  methods=["GET"])
def stream(identifier="output"):
    """ This endpoints streams stdout from a file expects
    the indetifier to be the file """
    output_file = os.path.join(current_app.config.get("TMPDIR"),
                               f"{identifier}.txt")
    seek_position = int(request.args.get("peak", 0))
    with open(output_file) as file_handler:
        # read to the last position default to 0
        file_handler.seek(seek_position)
        return jsonify({"data": file_handler.readlines(),
                        "run_id": identifier,
                        "pointer": file_handler.tell()})
