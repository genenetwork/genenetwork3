# pylint: disable=[R0902, R0903]
"""This contains all the necessary functions that access the metadata_audit
table from the db

"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MetadataAudit:
    """Data Type that represents a Phenotype"""
    dataset_id: int
    editor: str
    json_data: str
    time_stamp: Optional[str] = None


# Mapping from the MetadataAudit dataclass to the actual column names in the
# database
metadata_audit_mapping = {
    "dataset_id": "dataset_id",
    "editor": "editor",
    "json_data": "json_data",
    "time_stamp": "time_stamp",
}
