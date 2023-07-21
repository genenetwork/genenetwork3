"""Debug utilities"""

import logging

logger = logging.getLogger(__name__)

def __pk__(value, title="DEBUG"):
    """Peek the value and return it."""
    logger.debug("%s: %s", title, value)
    return value
