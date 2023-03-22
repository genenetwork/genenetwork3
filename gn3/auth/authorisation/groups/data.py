"""Handles the resource objects' data."""
from typing import Any, Sequence

from MySQLdb.cursors import DictCursor

from gn3 import db_utils as gn3db
from gn3.auth import db as authdb
from gn3.auth.authorisation.groups import Group
from gn3.auth.authorisation.checks import authorised_p
from gn3.auth.authorisation.errors import InvalidData, NotFoundError

def __fetch_grouped_data__(
        conn: authdb.DbConnection, dataset_type: str) -> Sequence[dict[str, Any]]:
    """Retrieve ids for all data that are linked to groups in the auth db."""
    with authdb.cursor(conn) as cursor:
        cursor.execute(
            "SELECT dataset_type, dataset_or_trait_id FROM linked_group_data "
            "WHERE LOWER(dataset_type)=?",
            (dataset_type,))
        return tuple(dict(row) for row in cursor.fetchall())

def __fetch_ungrouped_mrna_data__(
        conn: gn3db.Connection, grouped_data, offset: int) -> Sequence[dict]:
    """Fetch ungrouped mRNA Assay data."""
    query = ("SELECT psf.Id, psf.Name AS dataset_name, "
             "psf.FullName AS dataset_fullname, "
             "ifiles.GN_AccesionId AS accession_id FROM ProbeSetFreeze AS psf "
             "INNER JOIN InfoFiles AS ifiles ON psf.Name=ifiles.InfoPageName")
    params: tuple[Any, ...] = tuple()
    if bool(grouped_data):
        clause = ", ".join(["%s"] * len(grouped_data))
        query = f"{query} WHERE psf.Id NOT IN ({clause})"
        params = tuple(item["dataset_or_trait_id"] for item in grouped_data)

    query = f"{query} LIMIT 100 OFFSET %s"
    with conn.cursor(DictCursor) as cursor:
        cursor.execute(query, (params + (offset,)))
        return tuple(dict(row) for row in cursor.fetchall())

def __fetch_ungrouped_geno_data__(
        conn: gn3db.Connection, grouped_data, offset: int) -> Sequence[dict]:
    """Fetch ungrouped Genotype data."""
    query = ("SELECT gf.Id, gf.Name AS dataset_name, "
             "gf.FullName AS dataset_fullname, "
             "ifiles.GN_AccesionId AS accession_id FROM GenoFreeze AS gf "
             "INNER JOIN InfoFiles AS ifiles ON gf.Name=ifiles.InfoPageName")
    params: tuple[Any, ...] = tuple()
    if bool(grouped_data):
        clause = ", ".join(["%s"] * len(grouped_data))
        query = f"{query} WHERE gf.Id NOT IN ({clause})"
        params = tuple(item["dataset_or_trait_id"] for item in grouped_data)

    query = f"{query} LIMIT 100 OFFSET %s"
    with conn.cursor(DictCursor) as cursor:
        cursor.execute(query, (params + (offset,)))
        return tuple(dict(row) for row in cursor.fetchall())

def __fetch_ungrouped_pheno_data__(
        conn: gn3db.Connection, grouped_data, offset: int) -> Sequence[dict]:
    """Fetch ungrouped Phenotype data."""
    query = ("SELECT "
              "pxf.Id, iset.InbredSetName, pf.Name AS dataset_name, "
              "pf.FullName AS dataset_fullname, "
              "pf.ShortName AS dataset_shortname "
              "FROM PublishXRef AS pxf "
              "INNER JOIN InbredSet AS iset "
              "ON pxf.InbredSetId=iset.InbredSetId "
              "LEFT JOIN PublishFreeze AS pf "
              "ON iset.InbredSetId=pf.InbredSetId")
    params: tuple[Any, ...] = tuple()
    if bool(grouped_data):
        clause = ", ".join(["%s"] * len(grouped_data))
        query = f"{query} WHERE pxf.Id NOT IN ({clause})"
        params = tuple(item["dataset_or_trait_id"] for item in grouped_data)

    query = f"{query} LIMIT 100 OFFSET %s"
    with conn.cursor(DictCursor) as cursor:
        cursor.execute(query, (params + (offset,)))
        return tuple(dict(row) for row in cursor.fetchall())

def __fetch_ungrouped_data__(
        conn: gn3db.Connection, dataset_type: str,
        ungrouped: Sequence[dict[str, Any]],
        offset) -> Sequence[dict[str, Any]]:
    """Fetch any ungrouped data."""
    fetch_fns = {
        "mrna": __fetch_ungrouped_mrna_data__,
        "genotype": __fetch_ungrouped_geno_data__,
        "phenotype": __fetch_ungrouped_pheno_data__
    }
    return fetch_fns[dataset_type](conn, ungrouped, offset)

@authorised_p(("system:data:link-to-group",),
              error_description=(
                  "You do not have sufficient privileges to link data to (a) "
                  "group(s)."),
              oauth2_scope="profile group resource")
def retrieve_ungrouped_data(
        authconn: authdb.DbConnection,
        gn3conn: gn3db.Connection,
        dataset_type: str,
        offset: int = 0) -> Sequence[dict]:
    """Retrieve any data not linked to any group."""
    if dataset_type not in ("mrna", "genotype", "phenotype"):
        raise InvalidData(
            "Requested dataset type is invalid. Expected one of "
            "'mrna', 'genotype' or 'phenotype'.")
    grouped_data = __fetch_grouped_data__(authconn, dataset_type)
    return __fetch_ungrouped_data__(gn3conn, dataset_type, grouped_data, offset)

def __fetch_mrna_data_by_ids__(
        conn: gn3db.Connection, dataset_ids: tuple[str, ...]) -> tuple[
            dict, ...]:
    """Fetch mRNA Assay data by ID."""
    with conn.cursor(DictCursor) as cursor:
        paramstr = ", ".join(["%s"] * len(dataset_ids))
        cursor.execute(
            "SELECT psf.Id, psf.Name AS dataset_name, "
            "psf.FullName AS dataset_fullname, "
            "ifiles.GN_AccesionId AS accession_id FROM ProbeSetFreeze AS psf "
            "INNER JOIN InfoFiles AS ifiles ON psf.Name=ifiles.InfoPageName "
            f"WHERE psf.Id IN ({paramstr})",
            dataset_ids)
        res = cursor.fetchall()
        if res:
            return tuple(dict(row) for row in res)
        raise NotFoundError("Could not find mRNA Assay data with the given ID.")

def __fetch_geno_data_by_ids__(
        conn: gn3db.Connection, dataset_ids: tuple[str, ...]) -> tuple[
            dict, ...]:
    """Fetch genotype data by ID."""
    with conn.cursor(DictCursor) as cursor:
        paramstr = ", ".join(["%s"] * len(dataset_ids))
        cursor.execute(
            "SELECT gf.Id, gf.Name AS dataset_name, "
            "gf.FullName AS dataset_fullname, "
            "ifiles.GN_AccesionId AS accession_id FROM GenoFreeze AS gf "
            "INNER JOIN InfoFiles AS ifiles ON gf.Name=ifiles.InfoPageName "
            f"WHERE gf.Id IN ({paramstr})",
            dataset_ids)
        res = cursor.fetchall()
        if res:
            return tuple(dict(row) for row in res)
        raise NotFoundError("Could not find Genotype data with the given ID.")

def __fetch_pheno_data_by_ids__(
        conn: gn3db.Connection, dataset_ids: tuple[str, ...]) -> tuple[
            dict, ...]:
    """Fetch phenotype data by ID."""
    with conn.cursor(DictCursor) as cursor:
        paramstr = ", ".join(["%s"] * len(dataset_ids))
        cursor.execute(
            "SELECT pxf.Id, iset.InbredSetName, pf.Id AS dataset_id, "
            "pf.Name AS dataset_name, pf.FullName AS dataset_fullname, "
            "ifiles.GN_AccesionId AS accession_id "
            "FROM PublishXRef AS pxf "
            "INNER JOIN InbredSet AS iset ON pxf.InbredSetId=iset.InbredSetId "
            "INNER JOIN PublishFreeze AS pf ON iset.InbredSetId=pf.InbredSetId "
            "INNER JOIN InfoFiles AS ifiles ON pf.Name=ifiles.InfoPageName "
            f"WHERE pxf.Id IN ({paramstr})",
            dataset_ids)
        res = cursor.fetchall()
        if res:
            return tuple(dict(row) for row in res)
        raise NotFoundError(
            "Could not find Phenotype/Publish data with the given IDs.")

def __fetch_data_by_id(
        conn: gn3db.Connection, dataset_type: str,
        dataset_ids: tuple[str, ...]) -> tuple[dict, ...]:
    """Fetch data from MySQL by IDs."""
    fetch_fns = {
        "mrna": __fetch_mrna_data_by_ids__,
        "genotype": __fetch_geno_data_by_ids__,
        "phenotype": __fetch_pheno_data_by_ids__
    }
    return fetch_fns[dataset_type](conn, dataset_ids)

@authorised_p(("system:data:link-to-group",),
              error_description=(
                  "You do not have sufficient privileges to link data to (a) "
                  "group(s)."),
              oauth2_scope="profile group resource")
def link_data_to_group(
        authconn: authdb.DbConnection, gn3conn: gn3db.Connection,
        dataset_type: str, dataset_ids: tuple[str, ...], group: Group) -> tuple[
            dict, ...]:
    """Link the given data to the specified group."""
    the_data = __fetch_data_by_id(gn3conn, dataset_type, dataset_ids)
    with authdb.cursor(authconn) as cursor:
        params = tuple({
            "group_id": str(group.group_id), "dataset_type": {
                "mrna": "mRNA", "genotype": "Genotype",
                "phenotype": "Phenotype"
            }[dataset_type],
            "dataset_or_trait_id": item["Id"],
            "dataset_name": item["dataset_name"],
            "dataset_fullname": item["dataset_fullname"],
            "accession_id": item["accession_id"]
        } for item in the_data)
        cursor.executemany(
            "INSERT INTO linked_group_data VALUES"
            "(:group_id, :dataset_type, :dataset_or_trait_id, :dataset_name, "
            ":dataset_fullname, :accession_id)",
            params)
        return params
