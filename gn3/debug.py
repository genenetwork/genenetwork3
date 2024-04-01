"""Debug utilities"""
import logging
from flask import current_app

logger = logging.getLogger(__name__)

def __pk__(*args):
    value = args[-1]
    title_vals = " => ".join(args[0:-1])
    current_app.logger.setLevel(logging.DEBUG) # Force debug level since we assume we are using it!
    current_app.logger.debug("%s: %s", title_vals, value)
    return value
