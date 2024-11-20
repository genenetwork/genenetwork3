""" File contains the endpoints for calling rqtl2
"""

import subprocess
from flask import current_app
from flask import jsonify
from flask import Blueprint

rqtl2 = Blueprint("rqtl2", __name__)


@rqtl2.route("/compute", methods=["GET"])
def compute():
    """Init endpoint for computing qtl anaylsis using rqtl2"""
    # preprocessing data from the client
    # define required inputs
    # todo create a temp working directory for this
    wkdir = current_app.config.get("TMPDIR")
    rscript_command = f"Rscript  ./scripts/rqtl2_wrapper.R -i  /home/kabui/r_playground/meta_grav.json -d /home/kabui/r_playground  -o  /home/kabui/r_playground/rqtl_output.json  --nperm 1000  --threshold  1  --cores 0"
    p = subprocess.Popen(
        rscript_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    for line in iter(p.stdout.readline, b""):
        deco_line = line.decode("utf-8").strip()
        print(deco_line)
    p.wait()
    return jsonify({"data": []})
