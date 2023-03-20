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
        conn: gn3db.Connection, grouped_data,
        offset: int = 0) -> Sequence[dict]:
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
        conn: gn3db.Connection, grouped_data,
        offset: int = 0) -> Sequence[dict]:
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
        conn: gn3db.Connection, grouped_data,
        offset: int = 0) -> Sequence[dict]:
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
        ungrouped: Sequence[dict[str, Any]]) -> Sequence[dict[str, Any]]:
    """Fetch any ungrouped data."""
    fetch_fns = {
        "mrna": __fetch_ungrouped_mrna_data__,
        "genotype": __fetch_ungrouped_geno_data__,
        "phenotype": __fetch_ungrouped_pheno_data__
    }
    return fetch_fns[dataset_type](conn, ungrouped)

@authorised_p(("system:data:link-to-group",),
              error_description=(
                  "You do not have sufficient privileges to link data to (a) "
                  "group(s)."),
              oauth2_scope="profile group resource")
def retrieve_ungrouped_data(
        authconn: authdb.DbConnection,
        gn3conn: gn3db.Connection,
        dataset_type: str) -> Sequence[dict]:
    """Retrieve any data not linked to any group."""
    if dataset_type not in ("mrna", "genotype", "phenotype"):
        raise InvalidData(
            "Requested dataset type is invalid. Expected one of "
            "'mrna', 'genotype' or 'phenotype'.")
    grouped_data = __fetch_grouped_data__(authconn, dataset_type)
    return __fetch_ungrouped_data__(gn3conn, dataset_type, grouped_data)

def __fetch_mrna_data_by_id__(conn: gn3db.Connection, dataset_id: str) -> dict:
    """Fetch mRNA Assay data by ID."""
    with conn.cursor(DictCursor) as cursor:
        cursor.execute(
            "SELECT psf.Id, psf.Name, psf.FullName, "
            "ifiles.GN_AccesionId AS accession_id FROM ProbeSetFreeze AS psf "
            "INNER JOIN InfoFiles AS ifiles ON psf.Name=ifiles.InfoPageName "
            "WHERE psf.Id=%s",
            (dataset_id,))
        res = cursor.fetchone()
        if res:
            return dict(res)
        raise NotFoundError("Could not find mRNA Assay data with the given ID.")

def __fetch_geno_data_by_id__(conn: gn3db.Connection, dataset_id: str) -> dict:
    """Fetch genotype data by ID."""
    with conn.cursor(DictCursor) as cursor:
        cursor.execute(
            "SELECT gf.Id, gf.Name, gf.FullName, "
            "ifiles.GN_AccesionId AS accession_id FROM GenoFreeze AS gf "
            "INNER JOIN InfoFiles AS ifiles ON gf.Name=ifiles.InfoPageName "
            "WHERE gf.Id=%s",
            (dataset_id,))
        res = cursor.fetchone()
        if res:
            return dict(res)
        raise NotFoundError("Could not find Genotype data with the given ID.")

def __fetch_pheno_data_by_id__(conn: gn3db.Connection, dataset_id: str) -> dict:
    """Fetch phenotype data by ID."""
    with conn.cursor(DictCursor) as cursor:
        cursor.execute(
            "SELECT pf.Id, pf.Name, pf.FullName, "
            "ifiles.GN_AccesionId AS accession_id FROM PublishFreeze AS pf "
            "INNER JOIN InfoFiles AS ifiles ON pf.Name=ifiles.InfoPageName "
            "WHERE pf.Id=%s",
            (dataset_id,))
        res = cursor.fetchone()
        if res:
            return dict(res)
        raise NotFoundError(
            "Could not find Phenotype/Publish data with the given ID.")

def __fetch_data_by_id(
        conn: gn3db.Connection, dataset_type: str, dataset_id: str) -> dict:
    """Fetch data from MySQL by ID."""
    fetch_fns = {
        "mrna": __fetch_mrna_data_by_id__,
        "genotype": __fetch_geno_data_by_id__,
        "phenotype": __fetch_pheno_data_by_id__
    }
    return fetch_fns[dataset_type](conn, dataset_id)

@authorised_p(("system:data:link-to-group",),
              error_description=(
                  "You do not have sufficient privileges to link data to (a) "
                  "group(s)."),
              oauth2_scope="profile group resource")
def link_data_to_group(
        authconn: authdb.DbConnection, gn3conn: gn3db.Connection,
        dataset_type: str, dataset_id: str, group: Group) -> dict:
    """Link the given data to the specified group."""
    the_data = __fetch_data_by_id(gn3conn, dataset_type, dataset_id)
    with authdb.cursor(authconn) as cursor:
        params = {
            "group_id": str(group.group_id), "dataset_type": {
                "mrna": "mRNA", "genotype": "Genotype",
                "phenotype": "Phenotype"
            }[dataset_type],
            "dataset_or_trait_id": dataset_id, "dataset_name": the_data["Name"],
            "dataset_fullname": the_data["FullName"],
            "accession_id": the_data["accession_id"]
        }
        cursor.execute(
            "INSERT INTO linked_group_data VALUES"
            "(:group_id, :dataset_type, :dataset_or_trait_id, :dataset_name, "
            ":dataset_fullname, :accession_id)",
            params)
        return params
