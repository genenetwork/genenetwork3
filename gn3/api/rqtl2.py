""" File contains the endpoints for calling rqtl2
"""

import subprocess
import uuid
from flask import current_app
from flask import jsonify
from flask import Blueprint
from redis import Redis
from computations.rqtl2 import create_rqtl2_task
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


@rqtl2.route("/submit", methods=["GET"])
def submit():
    """Endpoint create an rqtl2 task and return a str id"""
    with Redis() as conn:
        task_id = create_rqtl2_task(conn)  # error to be caught by error.py app level
        return jsonify(task_id)


@rqtl2.route("/task/<task_id>", methods=["GET"])
def get_task(task_id):
    """Polling endpoint to fetch task_id and the metadata"""
    return {
        str(uuid.uuid4()): {
            "task_id": task_id,
            "results": [],
            "status": "queued",
            "stdout": "",
            "stderror": "",
        }
    }
