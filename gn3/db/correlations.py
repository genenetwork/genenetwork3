"""
This module will hold functions that are used in the (partial) correlations
feature to access the database to retrieve data needed for computations.
"""

from typing import Any
def get_filename(target_db_name: str, conn: Any) -> str:
    """
    Retrieve the name of the reference database file with which correlations are
    computed.

    This is a migration of the
    `web.webqtl.correlation.CorrelationPage.getFileName` function in
    GeneNetwork1.
    """
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT Id, FullName from ProbeSetFreeze WHERE Name-%s",
            target_db_name)
        result = cursor.fetchone()
        if result:
            return "ProbeSetFreezeId_{tid}_FullName_{fname}.txt".format(
                tid=result[0],
                fname=result[1].replace(' ', '_').replace('/', '_'))

    return ""
