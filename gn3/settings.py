"""Configuration settings for this project"""

import tempfile
import os

BCRYPT_SALT = "$2b$12$mxLvu9XRLlIaaSeDxt8Sle"  # Change this!
DATA_DIR = ""
GEMMA_WRAPPER_CMD = os.environ.get("GEMMA_WRAPPER", "gemma-wrapper")
RQTL_WRAPPER_CMD = os.environ.get("RQTL_WRAPPER")
CACHEDIR = ""
REDIS_URI = "redis://localhost:6379/0"
REDIS_JOB_QUEUE = "GN3::job-queue"
TMPDIR = os.environ.get("TMPDIR", tempfile.gettempdir())
RQTL_WRAPPER = "rqtl_wrapper.R"

# SQL confs
SQL_URI = os.environ.get(
    "SQL_URI", "mysql://webqtlout:webqtlout@localhost/db_webqtl")
SECRET_KEY = "password"
SQLALCHEMY_TRACK_MODIFICATIONS = False
# gn2 results only used in fetching dataset info

GN2_BASE_URL = "http://www.genenetwork.org/"

# biweight script
BIWEIGHT_RSCRIPT = "~/genenetwork3/script/calculate_biweight.R"
