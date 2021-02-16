"""General API endpoints.  Put endpoints that can't be grouped together nicely
here."""
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from gn3.file_utils import extract_uploaded_file


general = Blueprint("general", __name__)


@general.route("/metadata/upload", methods=["POST"])
def upload_metadata():
    """Extract uploaded file to gn3 temporary directory; and if successful return
a TOKEN to the user

    """
    file_ = request.files.get("file")
    if not file_:
        return jsonify(status=128, error="Please provide a file!"), 400

    status = 201
    results = extract_uploaded_file(
        gzipped_file=request.files["file"],
        target_dir=current_app.config["APP_DEFAULTS"].get("TMPDIR"))
    if results.get("status") > 0:
        status = 500
    return jsonify(results), status
