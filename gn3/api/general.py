"""General API endpoints.  Put endpoints that can't be grouped together nicely
here."""
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from gn3.file_utils import extract_uploaded_file


general = Blueprint("general", __name__)


@general.route("/metadata/upload")
def upload_metadata():
    """Extract uploaded file to gn3 temporary directory; and if successful return
a TOKEN to the user

    """
    results = extract_uploaded_file(gzipped_file=request.files["file"],
                                    target_dir=current_app.get("TMPDIR"))
    return jsonify(results)
