

from flask import g
from gn3.utility.logger import getLogger
logger = getLogger(__name__ )
# should probably put this is env
USE_GN_SERVER =False
def fetch1(query, path=None, func=None):
    if USE_GN_SERVER and path:
        results = gn_server(path)
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

    else:
        return fetchone(query)


def fetchone(query):
    def helper(query):
        res = g.db.execute(query)
        return res.fetchone()

    return logger.sql(query, helper)
