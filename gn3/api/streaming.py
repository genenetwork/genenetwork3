""" File contains endpoint for computational streaming"""
import os
from flask import current_app
from flask import jsonify
from flask import Blueprint
from flask import request

streaming = Blueprint("streaming", __name__)


@streaming.route("/stream/<identifier>",  methods=["GET"])
def stream(identifier="output"):
    """ This endpoints streams stdout from a file expects
    the indetifier to be the file """
    output_file = os.path.join(current_app.config.get("TMPDIR"),
                               f"{identifier}.txt")
    seek_position = int(request.args.get("peak", 0))
    with open(output_file, encoding="utf-8") as file_handler:
        # read to the last position default to 0
        file_handler.seek(seek_position)
        results = {"data": file_handler.readlines(),
                   "run_id": identifier,
                   "pointer": file_handler.tell()}
        return jsonify(results)
