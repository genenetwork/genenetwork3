# pylint: disable=[R0902, R0903]
"""This contains all the necessary functions that access the metadata_audit
table from the db

"""
import json
from typing import Optional
from dataclasses import dataclass

from MySQLdb.cursors import DictCursor

@dataclass(frozen=True)
class MetadataAudit:
    """Data Type that represents a Phenotype"""
    id_: Optional[int] = None
    dataset_id: Optional[int] = None
    editor: Optional[str] = None
    json_data: Optional[str] = None
    time_stamp: Optional[str] = None


# Mapping from the MetadataAudit dataclass to the actual column names in the
# database
metadata_audit_mapping = {
    "id_": "id",
    "dataset_id": "dataset_id",
    "editor": "editor",
    "json_data": "json_diff_data",
    "time_stamp": "time_stamp",
}

def create_metadata_audit(conn, metadata: dict) -> int:
    """Create a new metadata audit trail."""
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            "INSERT INTO metadata_audit (dataset_id, editor, json_diff_data) "
            "VALUES (%(dataset_id)s, %(editor)s, %(json_data)s)",
            metadata)
        return cursor.rowcount

def __parse_metadata_audit__(row) -> dict:
    """Convert values in DB to expected Python values """
    return {
        **{key:val for key,val in row.items() if key not in ("json_diff_data")},
        "id_": row["id"],
        "json_data": json.loads(row["json_diff_data"])
    }

def fetch_phenotype_metadata_audit_by_dataset_id(conn, dataset_id) -> tuple[dict, ...]:
    """Fetch phenotype a metadata audit trail by `dataset_id`."""
    assert bool(dataset_id), "`dataset_id` MUST be provided."
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            "SELECT ma.* "
            "FROM PublishXRef AS pxr LEFT JOIN metadata_audit AS ma "
            "ON pxr.Id=ma.dataset_id "
            "WHERE pxr.Id=%(dataset_id)s "
            "AND ma.json_diff_data LIKE '%%phenotype%%' "
            "ORDER BY time_stamp ASC",
            {"dataset_id": dataset_id})
        return tuple(__parse_metadata_audit__(row) for row in cursor.fetchall())

def fetch_probeset_metadata_audit_by_trait_name(conn, trait_name) -> tuple[dict, ...]:
    """Fetch a probeset metadata audit trail by `dataset_id`."""
    assert bool(dataset_id), "`dataset_id` MUST be provided."
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            "SELECT ma.* "
            "FROM ProbeSet AS ps LEFT JOIN metadata_audit AS ma "
            "ON ps.Id=ma.dataset_id "
            "WHERE ps.Name=%(trait_name)s "
            "AND json_diff_data LIKE '%probeset%' "
            "ORDER BY time_stamp ASCENDING",
            {"trait_name": trait_name})
        return tuple(__parse_metadata_audit__(row) for row in cursor.fetchall())
