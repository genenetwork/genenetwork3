"""Handles the resource objects' data."""
from typing import Any, Sequence

from MySQLdb.cursors import DictCursor

from gn3 import db_utils as gn3db
from gn3.auth import db as authdb
from gn3.auth.authorisation.errors import InvalidData

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
    query = ("SELECT psf.Id, psf.Name, psf.FullName, "
             "ifiles.GN_AccesionId AS accession_id FROM ProbeSetFreeze AS psf "
             "INNER JOIN InfoFiles AS ifiles ON psf.Name=ifiles.InfoPageName")
    params: tuple[Any, ...] = tuple()
    if bool(grouped_data):
        clause = ", ".join(["%s"] * len(grouped_data))
        query = f"{query} WHERE psf.Id NOT IN ({clause})"
        params = tuple(item["dataset_or_trait_id"] for item in grouped_data)

    query = f"{query} LIMIT 100 OFFSET %s"
    with conn.cursor(cursorclass=DictCursor) as cursor:# type: ignore[call-arg]
        cursor.execute(query, (params + (offset,)))
        return tuple(dict(row) for row in cursor.fetchall())

def __fetch_ungrouped_geno_data__(
        conn: gn3db.Connection, grouped_data,
        offset: int = 0) -> Sequence[dict]:
    """Fetch ungrouped Genotype data."""
    query = ("SELECT gf.Id, gf.Name, gf.FullName, "
             "ifiles.GN_AccesionId AS accession_id FROM GenoFreeze AS gf "
             "INNER JOIN InfoFiles AS ifiles ON gf.Name=ifiles.InfoPageName")
    params: tuple[Any, ...] = tuple()
    if bool(grouped_data):
        clause = ", ".join(["%s"] * len(grouped_data))
        query = f"{query} WHERE gf.Id NOT IN ({clause})"
        params = tuple(item["dataset_or_trait_id"] for item in grouped_data)

    query = f"{query} LIMIT 100 OFFSET %s"
    with conn.cursor(cursorclass=DictCursor) as cursor:# type: ignore[call-arg]
        cursor.execute(query, (params + (offset,)))
        return tuple(dict(row) for row in cursor.fetchall())

def __fetch_ungrouped_pheno_data__(
        conn: gn3db.Connection, grouped_data,
        offset: int = 0) -> Sequence[dict]:
    """Fetch ungrouped Phenotype data."""
    query = ("SELECT pf.Id, pf.Name, pf.FullName, "
             "ifiles.GN_AccesionId AS accession_id FROM PublishFreeze AS pf "
             "INNER JOIN InfoFiles AS ifiles ON pf.Name=ifiles.InfoPageName")
    params: tuple[Any, ...] = tuple()
    if bool(grouped_data):
        clause = ", ".join(["%s"] * len(grouped_data))
        query = f"{query} WHERE pf.Id NOT IN ({clause})"
        params = tuple(item["dataset_or_trait_id"] for item in grouped_data)

    query = f"{query} LIMIT 100 OFFSET %s"
    with conn.cursor(cursorclass=DictCursor) as cursor:# type: ignore[call-arg]
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
    print(f"GROUPED DATA: {grouped_data}")
    return __fetch_ungrouped_data__(gn3conn, dataset_type, grouped_data)
