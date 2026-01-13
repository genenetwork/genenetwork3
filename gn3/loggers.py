"""Setup loggers"""
import os
import sys
import logging
from logging import StreamHandler
from gn_libs.http_logging import SilentHTTPHandler  # type: ignore


logging.basicConfig(
    format=("%(asctime)s — %(filename)s:%(lineno)s — %(levelname)s "
            "(%(thread)d:%(threadName)s): %(message)s")
)


def loglevel(app):
    """'Compute' the LOGLEVEL from the application."""
    return logging.DEBUG if app.config.get("DEBUG", False) else logging.WARNING


def setup_modules_logging(level, modules):
    """Configure logging levels for a list of modules."""
    for module in modules:
        _logger = logging.getLogger(module)
        _logger.setLevel(level)


def __add_default_handlers__(app):
    """Add some default handlers, if running in dev environment."""
    node = "CD" if "auth-cd" in app.config.get("AUTH_SERVER_URL") else "Production"
    sheepdog_port = app.config.get("SHEEPDOG_PORT", 5050)
    http_handler = SilentHTTPHandler(
        endpoint = f"http://localhost:{sheepdog_port}/emit/{node}/genenetwork3"
    )
    stderr_handler = StreamHandler(stream=sys.stderr)
    app.logger.addHandler(stderr_handler)
    app.logger.addHandler(http_handler)
    root_logger = logging.getLogger()
    root_logger.addHandler(stderr_handler)
    root_logger.addHandler(http_handler)
    root_logger.setLevel(loglevel(app))


def __add_gunicorn_handlers__(app):
    """Set up logging for the WSGI environment with GUnicorn"""
    node = "CD" if "auth-cd" in app.config.get("AUTH_SERVER_URL") else "Production"
    sheepdog_port = app.config.get("SHEEPDOG_PORT", 5050)
    http_handler = SilentHTTPHandler(
        endpoint = f"http://localhost:{sheepdog_port}/emit/{node}/genenetwork3"
    )
    logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = logger.handlers
    app.logger.addHandler(http_handler)
    app.logger.setLevel(logger.level)
    return app


def setup_app_logging(app):
    """Setup the logging handlers for the application `app`."""
    software, *_version_and_comments = os.environ.get(
        "SERVER_SOFTWARE", "").split('/')
    return (__add_gunicorn_handlers__(app)
            if bool(software)
            else __add_default_handlers__(app))
