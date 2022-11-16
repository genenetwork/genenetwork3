"""Handle connection to auth database."""
import sqlite3
import contextlib
from typing import Any, Iterator, Protocol

import traceback

from flask import current_app as app

class DbConnection(Protocol):
    """Type annotation for a generic database connection object."""
    def cursor(self) -> Any:
        """A cursor object"""
        ...

    def commit(self) -> Any:
        """Commit the transaction."""
        ...

    def rollback(self) -> Any:
        """Rollback the transaction."""
        ...

class DbCursor(Protocol):
    """Type annotation for a generic database cursor object."""
    def execute(self, *args, **kwargs) -> Any:
        """Execute a single query"""
        ...

    def executemany(self, *args, **kwargs) -> Any:
        """
        Execute parameterized SQL statement sql against all parameter sequences
        or mappings found in the sequence parameters.
        """
        ...

    def fetchone(self, *args, **kwargs):
        """Fetch single result if present, or `None`."""
        ...

    def fetchmany(self, *args, **kwargs):
        """Fetch many results if present or `None`."""
        ...

    def fetchall(self, *args, **kwargs):
        """Fetch all results if present or `None`."""
        ...

@contextlib.contextmanager
def connection(db_path: str) -> Iterator[DbConnection]:
    """Create the connection to the auth database."""
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    except sqlite3.Error as exc:
        conn.rollback()
        app.logger.debug(traceback.format_exc())
        raise exc
    finally:
        conn.commit()
        conn.close()

@contextlib.contextmanager
def cursor(conn: DbConnection) -> Iterator[DbCursor]:
    """Get a cursor from the given connection to the auth database."""
    cur = conn.cursor()
    try:
        yield cur
    except sqlite3.Error as exc:
        conn.rollback()
        app.logger.debug(traceback.format_exc())
        raise exc
    finally:
        conn.commit()
        cur.close()
