"""module contains all db related stuff"""
import contextlib
import logging
from typing import Any, Iterator, Optional, Protocol, Tuple
from urllib.parse import urlparse
import MySQLdb as mdb
import xapian


def parse_db_url(sql_uri: str) -> Tuple:
    """function to parse SQL_URI env variable note:there\
    is a default value for SQL_URI so a tuple result is\
    always expected"""
    parsed_db = urlparse(sql_uri)
    return (
        parsed_db.hostname, parsed_db.username, parsed_db.password,
        parsed_db.path[1:], parsed_db.port)


# pylint: disable=missing-class-docstring, missing-function-docstring, too-few-public-methods
class Connection(Protocol):
    """Type Annotation for MySQLdb's connection object"""
    def cursor(self, *args, **kwargs) -> Any:
        """A cursor in which queries may be performed"""


@contextlib.contextmanager
def database_connection(sql_uri: str, logger: Optional[logging.Logger] = None) -> Iterator[Connection]:
    """Connect to MySQL database."""
    if logger is None:
        logger = logging.getLogger(__file__)
    host, user, passwd, db_name, port = parse_db_url(sql_uri)
    connection = mdb.connect(db=db_name,
                             user=user,
                             passwd=passwd or '',
                             host=host,
                             port=port or 3306)
    try:
        yield connection
    except mdb.Error as _mbde:
        logger.error("DB error encountered", exc_info=1)
        connection.rollback()
    finally:
        connection.commit()
        connection.close()


@contextlib.contextmanager
def xapian_database(path):
    """Open xapian database read-only."""
    # pylint: disable-next=invalid-name
    db = xapian.Database(path)
    try:
        yield db
    finally:
        db.close()
