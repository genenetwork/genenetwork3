"""module contains all db related stuff"""
from typing import Tuple
from urllib.parse import urlparse
import MySQLdb as mdb
from gn3.settings import SQL_URI


def parse_db_url() -> Tuple:
    """function to parse SQL_URI env variable note:there\
    is a default value for SQL_URI so a tuple result is\
    always expected"""
    parsed_db = urlparse(SQL_URI)
    return (parsed_db.hostname, parsed_db.username,
            parsed_db.password, parsed_db.path[1:])


def database_connector() -> Tuple:
    """function to create db connector"""
    host, user, passwd, db_name = parse_db_url()
    conn = mdb.connect(host, user, passwd, db_name)
    cursor = conn.cursor()

    return (conn, cursor)
