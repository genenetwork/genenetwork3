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

# wgcna script
WGCNA_RSCRIPT = "wgcna_analysis.R"
# qtlreaper command
REAPER_COMMAND = "{}/bin/qtlreaper".format(os.environ.get("GUIX_ENVIRONMENT"))

# genotype files
GENOTYPE_FILES = os.environ.get(
    "GENOTYPE_FILES", "{}/genotype_files/genotype".format(os.environ.get("HOME")))

# CROSS-ORIGIN SETUP
def parse_env_cors(default):
    """Parse comma-separated configuration into list of strings."""
    origins_str = os.environ.get("CORS_ORIGINS", None)
    if origins_str:
        return [
            origin.strip() for origin in origins_str.split(",") if origin != ""]
    return default

CORS_ORIGINS = parse_env_cors([
    "http://localhost:*",
    "http://127.0.0.1:*"
])

CORS_HEADERS = [
    "Content-Type",
    "Authorization",
    "Access-Control-Allow-Credentials"
]

GNSHARE = os.environ.get("GNSHARE", "/gnshare/gn/")
TEXTDIR = f"{GNSHARE}/web/ProbeSetFreeze_DataMatrix"

ROUND_TO = 10
