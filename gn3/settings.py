"""Configuration settings for this project"""

import tempfile
import os

BCRYPT_SALT = "$2b$12$mxLvu9XRLlIaaSeDxt8Sle"  # Change this!
DATA_DIR = ""
GEMMA_WRAPPER_CMD = os.environ.get("GEMMA_WRAPPER", "gemma-wrapper")
CACHEDIR = ""
REDIS_URI = "redis://localhost:6379/0"
REDIS_JOB_QUEUE = "GN3::job-queue"
TMPDIR = os.environ.get("TMPDIR", tempfile.gettempdir())

# SQL confs
SQLALCHEMY_DATABASE_URI = "mysql://kabui:1234@localhost/test"
SECRET_KEY = "password"
SQLALCHEMY_TRACK_MODIFICATIONS = False
