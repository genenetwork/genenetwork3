# pylint: disable=[R0902, R0903]
"""This contains all the necessary functions that access the metadata_audit
table from the db

"""
from dataclasses import dataclass
from typing import Optional


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
    "json_data": "json_data",
    "time_stamp": "time_stamp",
}
