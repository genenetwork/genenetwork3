"""module contains all db related stuff"""
from typing import Tuple
from urllib.parse import urlparse
import MySQLdb as mdb
from gn3.settings import SQL_URI


def parse_db_url(db_uri: str) -> Tuple:
    """function to parse SQL_URI env variable note:there\
    is a default value for SQL_URI so a tuple result is\
    always expected"""
    parsed_db = urlparse(db_uri)
    return (parsed_db.hostname, parsed_db.username, parsed_db.password,
            parsed_db.path[1:], parsed_db.port)


def database_connector(db_uri: str = SQL_URI) -> mdb.Connection:
    """function to create db connector"""
    return mdb.connect(**{
        key: val for key, val in
        dict(zip(
            ("host", "user", "passwd", "db", "port"),
            parse_db_url(db_uri))).items()
        if bool(val)
    })
