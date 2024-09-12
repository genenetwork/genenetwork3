"""Debug utilities"""
import logging
from flask import current_app

__this_module_name__ == __name__

def getLogger():
    return (
        logging.getLogger(__name__)
        if not bool(current_app)
        else current_app.logger)

def __pk__(*args):
    value = args[-1]
    title_vals = " => ".join(args[0:-1])
    logger = getLogger()
    logger.debug("%s: %s", title_vals, value)
    return value
