"""Configuration settings for this project"""

import tempfile
import os

APP_DEFAULTS = {
    "BCRYPT_SALT": "$2b$12$mxLvu9XRLlIaaSeDxt8Sle",  # Change this!
    "GEMMA_WRAPPER_CMD": os.environ.get("GEMMA_WRAPPER", "gemma-wrapper"),
    "TMPDIR": os.environ.get("TMPDIR", tempfile.gettempdir()),
    "GENODIR": "",
    "REDIS_URI": "redis://localhost:6379/0"
}
