"""General API endpoints.  Put endpoints that can't be grouped together nicely
here."""
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from gn3.file_utils import extract_uploaded_file


general = Blueprint("general", __name__)


@general.route("/metadata/upload/", methods=["POST"],
               strict_slashes=False)
def upload_metadata_with_no_token():
    """Extract uploaded file to a some TMPDIR/TOKEN/ with a TTL(Time To Live). The
TTL is set in the metadata file. If none is provided, the default is 1
week. Generate a TOKEN

    """
    file_ = request.files.get("file")
    if not file_:
        return jsonify(status=128, error="Please provide a file!"), 400
    status = 201
    results = extract_uploaded_file(
        gzipped_file=file_,
        target_dir=current_app.config["TMPDIR"],
        token=None)
    if results.get("status") > 0:
        status = 500
    return jsonify(results), status


@general.route("/metadata/upload/<token>", methods=["POST"],
               strict_slashes=False)
def upload_metadata(token):
    """Extract uploaded file to a some TMPDIR/TOKEN/ with a TTL(Time To Live). The
TTL is set in the metadata file. If none is provided, the default is 1 week.

    """
    file_ = request.files.get("file")
    if not file_:
        return jsonify(status=128, error="Please provide a file!"), 400
    status = 201
    results = extract_uploaded_file(
        gzipped_file=file_,
        target_dir=current_app.config["TMPDIR"],
        token=token)
    if results.get("status") > 0:
        status = 500
    return jsonify(results), status
