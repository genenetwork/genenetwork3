"""Debug utilities"""
import logging
logger = logging.getLogger(__name__)

def __pk__(*args):
    value = args[-1]
    title_vals = " => ".join(args[0:-1])
    logger.debug("%s: %s", title_vals, value)
    return value
