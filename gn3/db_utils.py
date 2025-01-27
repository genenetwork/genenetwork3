"""module contains all db related stuff"""
import logging
import contextlib
from urllib.parse import urlparse
from typing import Callable

import xapian

# XXXX: Replace instances that call db_utils.Connection or
# db_utils.database_connection with a direct call to gn_libs.
# pylint: disable=[W0611]
from gn_libs.mysqldb import Connection, database_connection  # type: ignore


LOGGER = logging.getLogger(__file__)


def __check_true__(val: str) -> bool:
    """Check whether the variable 'val' has the string value `true`."""
    return val.strip().lower() == "true"


def __parse_db_opts__(opts: str) -> dict:
    """Parse database options into their appropriate values.

    This assumes use of python-mysqlclient library."""
    allowed_opts = (
        "unix_socket", "connect_timeout", "compress", "named_pipe",
        "init_command", "read_default_file", "read_default_group",
        "cursorclass", "use_unicode", "charset", "collation", "auth_plugin",
        "sql_mode", "client_flag", "multi_statements", "ssl_mode", "ssl",
        "local_infile", "autocommit", "binary_prefix")
    conversion_fns: dict[str, Callable] = {
        **{opt: str for opt in allowed_opts},
        "connect_timeout": int,
        "compress": __check_true__,
        "use_unicode": __check_true__,
        # "cursorclass": __load_cursor_class__
        "client_flag": int,
        "multi_statements": __check_true__,
        # "ssl": __parse_ssl_options__,
        "local_infile": __check_true__,
        "autocommit": __check_true__,
        "binary_prefix": __check_true__
    }
    queries = tuple(filter(bool, opts.split("&")))
    if len(queries) > 0:
        keyvals: tuple[tuple[str, ...], ...] = tuple(
            tuple(item.strip() for item in query.split("="))
            for query in queries)

        def __check_opt__(opt):
            assert opt in allowed_opts, (
                f"Invalid database connection option ({opt}) provided.")
            return opt
        return {
            __check_opt__(key): conversion_fns[key](val)
            for key, val in keyvals
        }
    return {}


def parse_db_url(sql_uri: str) -> dict:
    """Parse the `sql_uri` variable into a dict of connection parameters."""
    parsed_db = urlparse(sql_uri)
    return {
        "host": parsed_db.hostname,
        "port": parsed_db.port or 3306,
        "user": parsed_db.username,
        "password": parsed_db.password,
        "database": parsed_db.path.strip("/").strip(),
        **__parse_db_opts__(parsed_db.query)
    }


@contextlib.contextmanager
def xapian_database(path):
    """Open xapian database read-only."""
    # pylint: disable-next=invalid-name
    db = xapian.Database(path)
    try:
        yield db
    finally:
        db.close()
