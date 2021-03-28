"""module contains all db related stuff"""
from typing import Tuple
import MySQLdb as mdb   # type: ignore


def database_connector(host="localhost",
                       user="",
                       passwd="1234",
                       db_name="db_webqtl")->Tuple:
    """function to create db connector"""
    conn = mdb.connect(host, user, passwd, db_name)
    cursor = conn.cursor()

    return (conn, cursor)


def execute_sql_query():
    """function for executing any sql query\
    and return required results"""
    return True
