"""Setup loggers"""
import sys
import logging
from logging import StreamHandler

# ========== Setup formatters ==========
# ========== END: Setup formatters ==========

def loglevel(app):
    """'Compute' the LOGLEVEL from the application."""
    return logging.DEBUG if app.config.get("DEBUG", False) else logging.WARNING

def setup_app_handlers(app):
    """Setup the logging handlers for the application `app`."""
    # ========== Setup handlers ==========
    stderr_handler = StreamHandler(stream=sys.stderr)
    stderr_handler.setLevel(loglevel(app))
    app.logger.addHandler(stderr_handler)
    # ========== END: Setup handlers ==========
    root_logger = logging.getLogger()
    root_logger.addHandler(stderr_handler)
