"""this function contains experimental db staff"""
from typing import Tuple
import MySQLdb as mdb   # type: ignore


def database_connector()->Tuple:
    """function to create db connector"""
    conn = mdb.connect("localhost", "kabui", "1234", "db_webqtl")
    cursor = conn.cursor()

    return (conn, cursor)
