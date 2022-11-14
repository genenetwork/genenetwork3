"""Handle connection to auth database."""
import sqlite3
import contextlib

@contextlib.contextmanager
def connection(db_path: str):
    connection = sqlite3.connect(db_path)
    try:
        yield connection
    finally:
        connection.close()

@contextlib.contextmanager
def cursor(connection):
    cur = connection.cursor()
    try:
        yield cur
    finally:
        cur.close()
