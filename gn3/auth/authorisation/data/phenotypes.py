"""Handle linking of Phenotype data to the Auth(entic|oris)ation system."""
import gn3.auth.db as authdb
import gn3.db_utils as gn3db
from gn3.auth.authorisation.checks import authorised_p

def linked_phenotype_data(conn: authdb.DbConnection) -> tuple[dict, ...]:
    """Retrieve phenotype data linked to user groups."""
    with authdb.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM linked_phenotype_data")
        return tuple(dict(row) for row in cursor.fetchall())
    return tuple()

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
            for row in linked_phenotype_data(authconn))
        paramstr = ", ".join(["(?, ?, ?, ?)"] * len(params))
        query = (
            "SELECT spc.SpeciesId, iset.InbredSetId, pf.Id AS PublishFreezeId, "
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
