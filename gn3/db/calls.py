"""module contains calls method for db"""
import json
import urllib
from flask import g
from gn3.utility.logger import getLogger
logger = getLogger(__name__)
# should probably put this is env
USE_GN_SERVER = False
LOG_SQL = False

GN_SERVER_URL = None


def fetch1(query, path=None, func=None):
    """fetch1 method"""
    if USE_GN_SERVER and path:
        result = gn_server(path)
        if func is not None:
            res2 = func(result)

        else:
            res2 = result

        if LOG_SQL:
            pass
            # should probably and logger
            # logger.debug("Replaced SQL call", query)

        # logger.debug(path,res2)
        return res2

    return fetchone(query)


def gn_server(path):
    """Return JSON record by calling GN_SERVER

    """
    res = urllib.request.urlopen(GN_SERVER_URL+path)
    rest = res.read()
    res2 = json.loads(rest)
    return res2


def fetchone(query):
    """method to fetchone item from  db"""
    def helper(query):
        res = g.db.execute(query)
        return res.fetchone()

    return logger.sql(query, helper)
