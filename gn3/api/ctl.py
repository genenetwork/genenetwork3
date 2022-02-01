"""module contains endpoints for ctl"""

from flask import Blueprint
from flask import request
from flask import jsonify

from gn3.computations.ctl import call_ctl_script

ctl = Blueprint("ctl", __name__)


@ctl.route("/run_ctl", methods=["POST"])
def run_ctl():
    """endpoint to run ctl
    input: request form object
    output:json object enum::(response,error)

    """
    ctl_data = request.json

    (cmd_results, response) = call_ctl_script(ctl_data)
    return (jsonify({
        "results": results
    }), 200) if response is not None else (jsonify({"error": str(cmd_results)}), 401)
