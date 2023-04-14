"""Handle linking of Phenotype data to the Auth(entic|oris)ation system."""
from typing import Any, Iterable

from MySQLdb.cursors import DictCursor

import gn3.auth.db as authdb
import gn3.db_utils as gn3db
from gn3.auth.authorisation.checks import authorised_p

def linked_phenotype_data(
        authconn: authdb.DbConnection, gn3conn: gn3db.Connection,
        species: str = "") -> Iterable[dict[str, Any]]:
    """Retrieve phenotype data linked to user groups."""
    authkeys = ("SpeciesId", "InbredSetId", "PublishFreezeId", "PublishXRefId")
    with (authdb.cursor(authconn) as authcursor,
          gn3conn.cursor(DictCursor) as gn3cursor):
        authcursor.execute("SELECT * FROM linked_phenotype_data")
        linked = tuple(tuple(row[key] for key in authkeys)
                       for row in authcursor.fetchall())
        paramstr = "".join(["(%s, %s, %s, %s)"] * len(linked))
        query = (
            "SELECT spc.SpeciesId, spc.SpeciesName, iset.InbredSetId, "
            "iset.InbredSetName, pf.Id AS PublishFreezeId, "
            "pf.Name AS dataset_name, pf.FullName AS dataset_fullname, "
            "pf.ShortName AS dataset_shortname, pxr.Id AS PublishXRefId "
            "FROM "
            "Species AS spc "
            "INNER JOIN InbredSet AS iset "
            "ON spc.SpeciesId=iset.SpeciesId "
            "INNER JOIN PublishFreeze AS pf "
            "ON iset.InbredSetId=pf.InbredSetId "
            "INNER JOIN PublishXRef AS pxr "
            "ON pf.InbredSetId=pxr.InbredSetId") + (
                " WHERE" if (len(linked) > 0 or bool(species)) else "") + (
                    (" (spc.SpeciesId, iset.InbredSetId, pf.Id, pxr.Id) "
                     f"NOT IN ({paramstr})") if len(linked) > 0 else "") + (
                        " AND"if len(linked) > 0 else "") + (
                        " spc.SpeciesName=%s" if bool(species) else "")
        params = linked + ((species,) if bool(species) else tuple())
        gn3cursor.execute(query, params)
        return (item for item in gn3cursor.fetchall())

@authorised_p(("system:data:link-to-group",),
              error_description=(
                  "You do not have sufficient privileges to link data to (a) "
                  "group(s)."),
              oauth2_scope="profile group resource")
def ungrouped_phenotype_data(
        authconn: authdb.DbConnection, gn3conn: gn3db.Connection):
    """Retrieve phenotype data that is not linked to any user group."""
    with gn3conn.cursor() as cursor:
        params = tuple(
            (row["SpeciesId"], row["InbredSetId"], row["PublishFreezeId"],
             row["PublishXRefId"])
            for row in linked_phenotype_data(authconn, gn3conn))
        paramstr = ", ".join(["(?, ?, ?, ?)"] * len(params))
        query = (
            "SELECT spc.SpeciesId, spc.SpeciesName, iset.InbredSetId, "
            "iset.InbredSetName, pf.Id AS PublishFreezeId, "
            "pf.Name AS dataset_name, pf.FullName AS dataset_fullname, "
            "pf.ShortName AS dataset_shortname, pxr.Id AS PublishXRefId "
            "FROM "
            "Species AS spc "
            "INNER JOIN InbredSet AS iset "
            "ON spc.SpeciesId=iset.SpeciesId "
            "INNER JOIN PublishFreeze AS pf "
            "ON iset.InbredSetId=pf.InbredSetId "
            "INNER JOIN PublishXRef AS pxr "
            "ON pf.InbredSetId=pxr.InbredSetId")
        if len(params) > 0:
            query = query + (
                f" WHERE (iset.InbredSetId, pf.Id, pxr.Id) NOT IN ({paramstr})")

        cursor.execute(query, params)
        return tuple(dict(row) for row in cursor.fetchall())

    return tuple()
