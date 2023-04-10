"""Handle linking of mRNA Assay data to the Auth(entic|oris)ation system."""
import uuid
from typing import Iterable
from MySQLdb.cursors import DictCursor

import gn3.auth.db as authdb
import gn3.db_utils as gn3db
from gn3.auth.dictify import dictify
from gn3.auth.authorisation.checks import authorised_p
from gn3.auth.authorisation.groups.models import Group

def linked_mrna_data(conn: authdb.DbConnection) -> Iterable[dict]:
    """Retrieve mRNA Assay data that is linked to user groups."""
    with authdb.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM linked_mrna_data")
        return (dict(row) for row in cursor.fetchall())

@authorised_p(("system:data:link-to-group",),
              error_description=(
                  "You do not have sufficient privileges to link data to (a) "
                  "group(s)."),
              oauth2_scope="profile group resource")
def ungrouped_mrna_data(# pylint: disable=[too-many-arguments]
        authconn: authdb.DbConnection, gn3conn: gn3db.Connection,
        search_query: str, selected: tuple[dict, ...] = tuple(),
        limit: int = 10000, offset: int = 0) -> tuple[
            dict, ...]:
    """Retrieve mrna data that is not linked to any user group."""
    params = tuple(
        (row["SpeciesId"], row["InbredSetId"], row["ProbeFreezeId"],
         row["ProbeSetFreezeId"])
        for row in linked_mrna_data(authconn)) + tuple(
                (row["SpeciesId"], row["InbredSetId"], row["ProbeFreezeId"],
                 row["ProbeSetFreezeId"])
                for row in selected)
    query = (
        "SELECT s.SpeciesId, iset.InbredSetId, iset.InbredSetName, "
        "pf.ProbeFreezeId, pf.Name AS StudyName, psf.Id AS ProbeSetFreezeId, "
        "psf.Name AS dataset_name, psf.FullName AS dataset_fullname, "
        "psf.ShortName AS dataset_shortname "
        "FROM Species AS s INNER JOIN InbredSet AS iset "
        "ON s.SpeciesId=iset.SpeciesId INNER JOIN ProbeFreeze AS pf "
        "ON iset.InbredSetId=pf.InbredSetId INNER JOIN ProbeSetFreeze AS psf "
        "ON pf.ProbeFreezeId=psf.ProbeFreezeId ") + (
            "WHERE " if (len(params) > 0 or bool(search_query)) else "")

    if len(params) > 0:
        paramstr = ", ".join(["(%s, %s, %s, %s)"] * len(params))
        query = query + (
            "(s.SpeciesId, iset.InbredSetId, pf.ProbeFreezeId, psf.Id) "
            f"NOT IN ({paramstr}) "
            ) + ("AND " if bool(search_query) else "")

    if bool(search_query):
        query = query + (
            "CONCAT(pf.Name, psf.Name, ' ', psf.FullName, ' ', psf.ShortName) "
            "LIKE %s ")
        params = params + ((f"%{search_query}%",),)# type: ignore[operator]

    query = query + f"LIMIT {int(limit)} OFFSET {int(offset)}"
    with gn3conn.cursor(DictCursor) as cursor:
        cursor.execute(
            query, tuple(item for sublist in params for item in sublist))
        return tuple(row for row in cursor.fetchall())

@authorised_p(
    ("system:data:link-to-group",),
    error_description=(
        "You do not have sufficient privileges to link data to (a) "
        "group(s)."),
    oauth2_scope="profile group resource")
def link_mrna_data(
        conn: authdb.DbConnection, group: Group, datasets: dict) -> dict:
    """Link genotye `datasets` to `group`."""
    with authdb.cursor(conn) as cursor:
        cursor.executemany(
            "INSERT INTO linked_mrna_data VALUES "
            "(:data_link_id, :group_id, :SpeciesId, :InbredSetId, "
            ":ProbeFreezeId, :ProbeSetFreezeId, :dataset_name, "
            ":dataset_fullname, :dataset_shortname) "
            "ON CONFLICT "
            "(SpeciesId, InbredSetId, ProbeFreezeId, ProbeSetFreezeId) "
            "DO NOTHING",
            tuple({
                "data_link_id": str(uuid.uuid4()),
                "group_id": str(group.group_id),
                **{
                    key: value for key,value in dataset.items() if key in (
                        "SpeciesId", "InbredSetId", "ProbeFreezeId",
                        "ProbeSetFreezeId", "dataset_fullname", "dataset_name",
                        "dataset_shortname")
                }
            } for dataset in datasets))
        return {
            "description": (
                f"Successfully linked {len(datasets)} to group "
                f"'{group.group_name}'."),
            "group": dictify(group),
            "datasets": datasets
        }
