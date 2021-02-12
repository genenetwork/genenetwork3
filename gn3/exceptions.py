"""GN3 custom exceptions"""


class FailedToQueue(Exception):
    """Raised when a queueing operation fails"""


class RedisConnectionError(ConnectionError):
    """Raised when there is no Redis connection"""
