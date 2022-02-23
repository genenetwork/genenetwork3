"""Functions and classes that deal with responses and conversion to JSON."""
import json

from flask import make_response

class OutputEncoder(json.JSONEncoder):
    """
    Class to encode output into JSON, for objects which the default
    json.JSONEncoder class does not have default encoding for.
    """
    def default(self, o):
        if isinstance(o, bytes):
            return str(o, encoding="utf-8")
        return json.JSONEncoder.default(self, o)

def build_response(data):
    """Build the responses for the API"""
    status_codes = {
        "error": 400, "not-found": 404, "success": 200, "exception": 500}
    response = make_response(
            json.dumps(data, cls=OutputEncoder),
            status_codes[data["status"]])
    response.headers["Content-Type"] = "application/json"
    return response
