"""
Default configuration settings for this project.

DO NOT import from this file, use `flask.current_app.config` instead to get the
application settings.
"""
import os
import uuid
import tempfile

BCRYPT_SALT = "$2b$12$mxLvu9XRLlIaaSeDxt8Sle"  # Change this!
DATA_DIR = ""
GEMMA_WRAPPER_CMD = os.environ.get("GEMMA_WRAPPER", "gemma-wrapper")
RQTL_WRAPPER_CMD = os.environ.get("RQTL_WRAPPER")
CACHEDIR = ""
REDIS_URI = "redis://localhost:6379/0"
REDIS_JOB_QUEUE = "GN3::job-queue"
TMPDIR = os.environ.get("TMPDIR", tempfile.gettempdir())
RQTL_WRAPPER = "rqtl_wrapper.R"

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
# gn2 results only used in fetching dataset info

GN2_BASE_URL = "http://www.genenetwork.org/"

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

MULTIPROCESSOR_PROCS = 6 # Number of processes to spawn

AUTH_SERVER_URL=""
AUTH_MIGRATIONS = "migrations/auth"
AUTH_DB = os.environ.get(
    "AUTH_DB", f"{os.environ.get('HOME')}/genenetwork/gn3_files/db/auth.db")
OAUTH2_SCOPE = (
    "profile", "group", "role", "resource", "user", "masquerade",
    "introspect")

try:
    # *** SECURITY CONCERN ***
    # Clients with access to this privileges create a security concern.
    # Be careful when adding to this configuration
    OAUTH2_CLIENTS_WITH_INTROSPECTION_PRIVILEGE = tuple(
        uuid.UUID(client_id) for client_id in
        os.environ.get(
            "OAUTH2_CLIENTS_WITH_INTROSPECTION_PRIVILEGE", "").split(","))
except ValueError as _valerr:
    OAUTH2_CLIENTS_WITH_INTROSPECTION_PRIVILEGE = tuple()

try:
    # *** SECURITY CONCERN ***
    # Clients with access to this privileges create a security concern.
    # Be careful when adding to this configuration
    OAUTH2_CLIENTS_WITH_DATA_MIGRATION_PRIVILEGE = tuple(
        uuid.UUID(client_id) for client_id in
        os.environ.get(
            "OAUTH2_CLIENTS_WITH_DATA_MIGRATION_PRIVILEGE", "").split(","))
except ValueError as _valerr:
    OAUTH2_CLIENTS_WITH_DATA_MIGRATION_PRIVILEGE = tuple()
