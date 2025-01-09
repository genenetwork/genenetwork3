""" File contains endpoint for computational streaming"""
import os
from flask import current_app
from flask import jsonify
from flask import Blueprint
from flask import request

streaming = Blueprint("stream", __name__)


@streaming.route("/<identifier>",  methods=["GET"])
def stream(identifier):
    """ This endpoint streams stdout from a file.
    It expects the identifier to be the filename
    in the TMPDIR created at the main computation
    endpoint see example api/rqtl."""
    output_file = os.path.join(current_app.config.get("TMPDIR"),
                               f"{identifier}.txt")
    seek_position = int(request.args.get("peak", 0))
    with open(output_file, encoding="utf-8") as file_handler:
        # read from the last  read position default to 0
        file_handler.seek(seek_position)
        results = {"data": file_handler.readlines(),
                   "run_id": identifier,
                   "pointer": file_handler.tell()}
        return jsonify(results)
