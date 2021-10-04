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
BIWEIGHT_RSCRIPT = "~/genenetwork3/scripts/calculate_biweight.R"

# wgcna script
WGCNA_RSCRIPT = "wgcna_analysis.R"
# qtlreaper command
REAPER_COMMAND = "{}/bin/qtlreaper".format(os.environ.get("GUIX_ENVIRONMENT"))

# genotype files
GENOTYPE_FILES = os.environ.get(
    "GENOTYPE_FILES", "{}/genotype_files/genotype".format(os.environ.get("HOME")))

# CROSS-ORIGIN SETUP
CORS_ORIGINS = [
    "http://localhost:*",
    "http://127.0.0.1:*"
]

CORS_HEADERS = [
    "Content-Type",
    "Authorization",
    "Access-Control-Allow-Credentials"
]
