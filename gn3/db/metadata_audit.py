# pylint: disable=[R0902, R0903]
"""This contains all the necessary functions that access the metadata_audit
table from the db

"""
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
