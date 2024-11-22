""" File contains endpoints for rqlt2"""

import subprocess
import uuid
import os
from flask import current_app
from flask import jsonify
from flask import Blueprint

rqtl2 = Blueprint("rqtl2", __name__)

@rqtl2.route("/compute", methods=["GET"])
def compute():
    """Endpoint for computing QTL analysis using R/QTL2"""
    wkdir = current_app.config.get("TMPDIR")
    output_file = os.path.join(wkdir, "output.txt")
    rscript_cmd = (
        f"Rscript ./scripts/rqtl2_wrapper.R "
        f"-i /home/kabui/r_playground/meta_grav.json "
        f"-d /home/kabui/r_playground "
        f"-o /home/kabui/r_playground/rqtl_output.json "
        f"--nperm 100 --threshold 1 --cores 0"
    )
    process = subprocess.Popen(
        rscript_cmd, shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    # TODO rethink where we write this file
    with open(output_file, "a+") as file_handler:
        for line in iter(process.stdout.readline, b""):
            file_handler.write(line.decode("utf-8"))
    process.stdout.close()
    process.wait()
    if process.returncode == 0:
        return jsonify({"msg": "success", "results": "file_here"})
    else:
        return jsonify({"msg": "fail", "error": "Process failed"})


@rqtl2.route("/stream/<indetifier>",  methods=["GET"])
def stream(indetifier):
    """ This endpoints streams stdout from a file expects
    the indetifier to be the file """
    output_file = os.path.join(current_app.config.get("TMPDIR"),
                               f"{indetifier}.txt")
    # raise error if file does not exist
    with open(output_file) as file_handler:
        # rethink how we do the read should this be stream / yield ????
        return jsonify({"data": file_handler.readlines()})
