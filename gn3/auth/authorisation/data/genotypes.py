"""Handle linking of Genotype data to the Auth(entic|oris)ation system."""
from typing import Iterable

from MySQLdb.cursors import DictCursor

import gn3.auth.db as authdb
import gn3.db_utils as gn3db
from gn3.auth.authorisation.checks import authorised_p

def linked_genotype_data(conn: authdb.DbConnection) -> Iterable[dict]:
    """Retrive genotype data that is linked to user groups."""
    with authdb.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM linked_genotype_data")
        return (dict(row) for row in cursor.fetchall())

@authorised_p(("system:data:link-to-group",),
              error_description=(
                  "You do not have sufficient privileges to link data to (a) "
                  "group(s)."),
              oauth2_scope="profile group resource")
def ungrouped_genotype_data(
        authconn: authdb.DbConnection, gn3conn: gn3db.Connection,
        search_query: str, limit: int = 10000, offset: int = 0) -> tuple[
            dict, ...]:
    """Retrieve genotype data that is not linked to any user group."""
    params = tuple(
        (row["SpeciesId"], row["InbredSetId"], row["GenoFreezeId"])
            for row in linked_genotype_data(authconn))
    query = (
        "SELECT s.SpeciesId, iset.InbredSetId, iset.InbredSetName, "
        "gf.Id AS GenoFreezeId, gf.Name AS dataset_name, "
        "gf.FullName AS dataset_fullname, "
        "gf.ShortName AS dataset_shortname "
        "FROM Species AS s INNER JOIN InbredSet AS iset "
        "ON s.SpeciesId=iset.SpeciesId INNER JOIN GenoFreeze AS gf "
        "ON iset.InbredSetId=gf.InbredSetId ")

    if len(params) > 0 or bool(search_query):
        query = query + "WHERE "

    if len(params) > 0:
        paramstr = ", ".join(["(?, ?, ?)"] * len(params))
        query = query + (
            "(s.SpeciesId, iset.InbredSetId, GenoFreezeId) "
            f"NOT IN ({paramstr}) "
            "AND ")

    if bool(search_query):
        query = query + (
            "CONCAT(gf.Name, ' ', gf.FullName, ' ', gf.ShortName) LIKE '%%?%%' ")
        params = params + ((search_query,),)# type: ignore[operator]

    query = query + f"LIMIT {int(limit)} OFFSET {int(offset)}"
    with gn3conn.cursor(DictCursor) as cursor:
        cursor.execute(
            query, tuple(item for sublist in params for item in sublist))
        return tuple(row for row in cursor.fetchall())
