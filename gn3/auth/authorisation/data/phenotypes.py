"""Handle linking of Phenotype data to the Auth(entic|oris)ation system."""
import uuid
from typing import Any, Iterable

from MySQLdb.cursors import DictCursor

import gn3.auth.db as authdb
import gn3.db_utils as gn3db
from gn3.auth.dictify import dictify
from gn3.auth.authorisation.checks import authorised_p
from gn3.auth.authorisation.groups.models import Group

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
        if len(linked) <= 0:
            return iter(())
        paramstr = ", ".join(["(%s, %s, %s, %s)"] * len(linked))
        query = (
            "SELECT spc.SpeciesId, spc.Name AS SpeciesName, iset.InbredSetId, "
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
                     f"IN ({paramstr})") if len(linked) > 0 else "") + (
                        " AND"if len(linked) > 0 else "") + (
                        " spc.SpeciesName=%s" if bool(species) else "")
        params = tuple(item for sublist in linked for item in sublist) + (
            (species,) if bool(species) else tuple())
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

def __traits__(gn3conn: gn3db.Connection, params: tuple[dict, ...]) -> tuple[dict, ...]:
    """An internal utility function. Don't use outside of this module."""
    if len(params) < 1:
        return tuple()
    paramstr = ", ".join(["(%s, %s, %s, %s)"] * len(params))
    with gn3conn.cursor(DictCursor) as cursor:
        cursor.execute(
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
            "ON pf.InbredSetId=pxr.InbredSetId "
            "WHERE (spc.SpeciesName, iset.InbredSetName, pf.Name, pxr.Id) "
            f"IN ({paramstr})",
            tuple(
                itm for sublist in (
                    (item["species"], item["group"], item["dataset"], item["name"])
                    for item in params)
                for itm in sublist))
        return cursor.fetchall()

@authorised_p(("system:data:link-to-group",),
              error_description=(
                  "You do not have sufficient privileges to link data to (a) "
                  "group(s)."),
              oauth2_scope="profile group resource")
def link_phenotype_data(
        authconn:authdb.DbConnection, gn3conn: gn3db.Connection, group: Group,
        traits: tuple[dict, ...]) -> dict:
    """Link phenotype traits to a user group."""
    with authdb.cursor(authconn) as cursor:
        params = tuple({
            "data_link_id": str(uuid.uuid4()),
            "group_id": str(group.group_id),
            **item
        } for item in __traits__(gn3conn, traits))
        cursor.executemany(
            "INSERT INTO linked_phenotype_data "
            "VALUES ("
            ":data_link_id, :group_id, :SpeciesId, :InbredSetId, "
            ":PublishFreezeId, :dataset_name, :dataset_fullname, "
            ":dataset_shortname, :PublishXRefId"
            ")",
            params)
        return {
            "description": (
                f"Successfully linked {len(traits)} traits to group."),
            "group": dictify(group),
            "traits": params
        }
