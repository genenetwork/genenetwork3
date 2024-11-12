"""
Default configuration settings for this project.

DO NOT import from this file, use `flask.current_app.config` instead to get the
application settings.
"""
import os
import tempfile

BCRYPT_SALT = ""
DATA_DIR = ""
GEMMA_WRAPPER_CMD = os.environ.get("GEMMA_WRAPPER", "gemma-wrapper")
CACHEDIR = ""
REDIS_URI = "redis://localhost:6379/0"
REDIS_JOB_QUEUE = "GN3::job-queue"
TMPDIR = os.environ.get("TMPDIR", tempfile.gettempdir())

# SPARQL endpoint
SPARQL_ENDPOINT = os.environ.get(
    "SPARQL_ENDPOINT",
    "http://localhost:9082/sparql")

# LMDB path
LMDB_PATH = os.environ.get(
    "LMDB_PATH", f"{os.environ.get('HOME')}/tmp/dataset")

# SQL confs
SQL_URI = os.environ.get(
    "SQL_URI", "mysql://webqtlout:webqtlout@localhost/db_webqtl")
SECRET_KEY = "password"

# FAHAMU API TOKEN
FAHAMU_AUTH_TOKEN = ""

# wgcna script
WGCNA_RSCRIPT = "wgcna_analysis.R"
# qtlreaper command
REAPER_COMMAND = f"{os.environ.get('GUIX_ENVIRONMENT')}/bin/qtlreaper"

# correlation command

CORRELATION_COMMAND = f"{os.environ.get('GN2_PROFILE')}/bin/correlation_rust"

# genotype files
GENOTYPE_FILES = os.environ.get(
    "GENOTYPE_FILES", f"{os.environ.get('HOME')}/genotype_files/genotype")

# Xapian index
XAPIAN_DB_PATH = "xapian"

# sqlite path

LLM_DB_PATH = ""
# CROSS-ORIGIN SETUP


def parse_env_cors(default):
    """Parse comma-separated configuration into list of strings."""
    origins_str = os.environ.get("CORS_ORIGINS", None)
    if origins_str:
        return [
            origin.strip() for origin in origins_str.split(",") if origin != ""]
    return default


CORS_ORIGINS = parse_env_cors("*")

CORS_HEADERS = [
    "Content-Type",
    "Authorization",
    "Access-Control-Allow-Credentials"
]

GNSHARE = os.environ.get("GNSHARE", "/gnshare/gn/")
TEXTDIR = f"{GNSHARE}/web/ProbeSetFreeze_DataMatrix"

ROUND_TO = 10

MULTIPROCESSOR_PROCS = 6  # Number of processes to spawn

AUTH_SERVER_URL = ""
