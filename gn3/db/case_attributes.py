"""Module that contains functions for editing case-attribute data"""
from pathlib import Path
from typing import Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum, auto

import os
import json
import pickle
import lmdb
import MySQLdb


@dataclass
class CaseAttributeEdit:
    """Represents an edit operation for case attributes in the database.

    Attributes:
        inbredset_id (int): The ID of the inbred set associated with
        the edit.
        user_id (str): The ID of the user performing the edit.
        changes (dict): A dictionary containing the changes to be
    applied to the case attributes.

    """
    inbredset_id: int
    user_id: str
    changes: dict


class EditStatus(Enum):
    """Enumeration for the status of the edits."""
    review = auto()   # pylint: disable=[invalid-name]
    approved = auto()  # pylint: disable=[invalid-name]
    rejected = auto()  # pylint: disable=[invalid-name]

    def __str__(self):
        """Print out human-readable form."""
        return self.name


def queue_edit(cursor, directory: Path, edit: CaseAttributeEdit) -> int:
    """Queues a case attribute edit for review by inserting it into
    the audit table and storing its review ID in an LMDB database.

    Args:
        cursor: A database cursor for executing SQL queries.
        directory (Path): The base directory path for the LMDB database.
        edit (CaseAttributeEdit): A dataclass containing the edit details, including
            inbredset_id, user_id, and changes.

    Returns:
        int: An id the particular case-attribute that was updated.

    Notes:
        - Inserts the edit into the `caseattributes_audit` table with status set to
          `EditStatus.review`.
        - Uses LMDB to store review IDs under the key b"review" for the given
          inbredset_id.
        - The LMDB map_size is set to 8 MB.
    """
    cursor.execute(
        "INSERT INTO "
        "caseattributes_audit(status, editor, json_diff_data) "
        "VALUES (%s, %s, %s) "
        "ON DUPLICATE KEY UPDATE status=%s",
        (str(EditStatus.review),
         edit.user_id, json.dumps(edit.changes), str(EditStatus.review),))
    directory = f"{directory}/case-attributes/{edit.inbredset_id}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    env = lmdb.open(directory, map_size=8_000_000)  # 1 MB
    with env.begin(write=True) as txn:
        review_ids = set()
        if reviews := txn.get(b"review"):
            review_ids = pickle.loads(reviews)
        review_ids.add(cursor.lastrowid)
        txn.put(b"review", pickle.dumps(review_ids))
        return review_ids


def approve_case_attribute(conn: Any, case_attr_audit_id: int) -> int:
    """Given the id of the json_diff in the case_attribute_audit table,
    approve it

    """
    rowcount = 0
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT json_diff_data FROM caseattributes_audit "
                "WHERE id = %s",
                (case_attr_audit_id,),
            )
            diff_data = cursor.fetchone()
            if diff_data:
                diff_data = json.loads(diff_data[0])
                # Insert (Most Important)
                if diff_data.get("Insert"):
                    data = diff_data.get("Insert")
                    cursor.execute(
                        "INSERT INTO CaseAttribute "
                        "(Name, Description) VALUES "
                        "(%s, %s)",
                        (
                            data.get("name").strip(),
                            data.get("description").strip(),
                        ),
                    )
                # Delete
                elif diff_data.get("Deletion"):
                    data = diff_data.get("Deletion")
                    cursor.execute(
                        "DELETE FROM CaseAttribute WHERE Id = %s",
                        (data.get("id"),),
                    )
                # Modification
                elif diff_data.get("Modification"):
                    data = diff_data.get("Modification")
                    if desc_ := data.get("description"):
                        cursor.execute(
                            "UPDATE CaseAttribute SET "
                            "Description = %s WHERE Id = %s",
                            (
                                desc_.get("Current"),
                                diff_data.get("id"),
                            ),
                        )
                    if name_ := data.get("name"):
                        cursor.execute(
                            "UPDATE CaseAttribute SET "
                            "Name = %s WHERE Id = %s",
                            (
                                name_.get("Current"),
                                diff_data.get("id"),
                            ),
                        )
                if cursor.rowcount:
                    cursor.execute(
                        "UPDATE caseattributes_audit SET "
                        "status = 'approved' WHERE id = %s",
                        (case_attr_audit_id,),
                    )
            rowcount = cursor.rowcount
    except Exception as _e:
        raise MySQLdb.Error(_e) from _e
    return rowcount
