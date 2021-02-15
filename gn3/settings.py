"""Configuration settings for this project"""

import tempfile
import os

APP_DEFAULTS = {
    "GEMMA_WRAPPER_CMD": os.environ.get("GEMMA_WRAPPER", "gemma-wrapper"),
    "TMPDIR": os.environ.get("TMPDIR", tempfile.gettempdir()),
    "REDIS_URI": "redis://localhost:6379/0"
}
