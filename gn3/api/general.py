"""General API endpoints.  Put endpoints that can't be grouped together nicely
here."""
import os
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from gn3.fs_helpers import extract_uploaded_file
from gn3.commands import run_cmd


general = Blueprint("general", __name__)

@general.route("/version")
def version():
    """Get API version."""
    return jsonify("1.0")

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


@general.route("/qtl/run/<geno_filestr>/<pheno_filestr>",
               methods=["POST"],
               strict_slashes=False)
def run_r_qtl(geno_filestr, pheno_filestr):
    """Run r_qtl command using the written rqtl_wrapper program

    """
    rqtl_wrapper = 'scripts/rqtl_wrapper.R' # This is a stub
    cmd = (f"Rscript {rqtl_wrapper} "
           f"{geno_filestr} {pheno_filestr}")
    return jsonify(run_cmd(cmd)), 201


@general.route("/stream ",  methods=["GET"])
def stream():
    """
    This endpoint streams the stdout content from a file.
    It expects an identifier to be passed as a query parameter.
    Example: `/stream?id=<identifier>`
   The `id` will be used to locate the corresponding file.
   You can also pass an optional `peak` parameter
    to specify the file position to start reading from.
   Query Parameters:
   - `id` (required): The identifier used to locate the file.
   - `peak` (optional): The position in the file to start reading from.
   Returns:
   - dict with data(stdout), run_id unique id for file,
    pointer last read position for file
  """
    run_id = request.args.get("id", "")
    output_file = os.path.join(current_app.config.get("TMPDIR"),
                               f"{run_id}.txt")
    seek_position = int(request.args.get("peak", 0))
    with open(output_file, encoding="utf-8") as file_handler:
        # read to the last position default to 0
        file_handler.seek(seek_position)
        return jsonify({"data": file_handler.readlines(),
                        "run_id": run_id,
                        "pointer": file_handler.tell()})
