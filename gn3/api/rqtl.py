import os

from flask import Blueprint
from flask import current_app
from flask import request

rqtl = Blueprint("rqtl", __name__)

@rqtl.route("/compute", methods=["POST"])
def compute():
    working_dir = os.path.join(current_app.config.get("TMPDIR"))

    genofile = request.form['geno_file']
    phenofile = request.form['pheno_file']

    if not do_paths_exist([genofile, phenofile]):
        raise FileNotFoundError

    return current_app.config.get("RQTL_WRAPPER_CMD")