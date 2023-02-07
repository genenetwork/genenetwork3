"""Some common auth db utilities"""
from typing import Any, Callable
from flask import current_app

from . import db

def with_db_connection(func: Callable[[db.DbConnection], Any]) -> Any:
    """
    Takes a function of one argument `func`, whose one argument is a database
    connection.
    """
    db_uri = current_app.config["AUTH_DB"]
    with db.connection(db_uri) as conn:
        return func(conn)
