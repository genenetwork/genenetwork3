"""module for db_tools"""
from MySQLdb import escape_string as escape_


def create_in_clause(items):
    """Create an in clause for mysql"""
    in_clause = ', '.join("'{}'".format(x) for x in mescape(*items))
    in_clause = '( {} )'.format(in_clause)
    return in_clause


def mescape(*items):
    """Multiple escape"""
    return [escape_(str(item)).decode('utf8') for item in items]


def escape(string_):
    """escape function"""
    return escape_(string_).decode('utf8')
