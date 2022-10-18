"""module contains all db related stuff"""
import contextlib
from typing import Any, Iterator, Protocol, Tuple
from urllib.parse import urlparse
import MySQLdb as mdb
from gn3.settings import SQL_URI


def parse_db_url() -> Tuple:
    """function to parse SQL_URI env variable note:there\
    is a default value for SQL_URI so a tuple result is\
    always expected"""
    parsed_db = urlparse(SQL_URI)
    return (
        parsed_db.hostname, parsed_db.username, parsed_db.password,
        parsed_db.path[1:], parsed_db.port)


# This function is deprecated. Use database_connection instead.
def database_connector() -> mdb.Connection:
    """function to create db connector"""
    host, user, passwd, db_name, db_port = parse_db_url()

    return mdb.connect(host, user, passwd, db_name, port=(db_port or 3306))


class Connection(Protocol):
    def cursor(self) -> Any:
        ...


@contextlib.contextmanager
def database_connection() -> Iterator[Connection]:
    """Connect to MySQL database."""
    host, user, passwd, db_name, port = parse_db_url()
    connection = mdb.connect(db=db_name,
                             user=user,
                             passwd=passwd or '',
                             host=host,
                             port=port or 3306)
    try:
        yield connection
    finally:
        connection.close()
