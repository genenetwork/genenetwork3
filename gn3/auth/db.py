"""Handle connection to auth database."""
import sqlite3
import contextlib

@contextlib.contextmanager
def connection(db_path: str):
    """Create the connection to the auth database."""
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    except: # pylint: disable=bare-except
        conn.rollback()
    finally:
        conn.commit()
        conn.close()

@contextlib.contextmanager
def cursor(conn):
    """Get a cursor from the given connection to the auth database."""
    cur = conn.cursor()
    try:
        yield cur
    except: # pylint: disable=bare-except
        conn.rollback()
    finally:
        conn.commit()
        cur.close()
