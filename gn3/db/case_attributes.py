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


class EditStatus(Enum):
    """Enumeration for the status of the edits."""
    review = auto()   # pylint: disable=[invalid-name]
    approved = auto()  # pylint: disable=[invalid-name]
    rejected = auto()  # pylint: disable=[invalid-name]

    def __str__(self):
        """Print out human-readable form."""
        return self.name


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
    status: EditStatus
    user_id: str
    changes: dict


def queue_edit(cursor, directory: Path, edit: CaseAttributeEdit) -> Optional[int]:
    """Queues a case attribute edit for review by inserting it into
    the audit table and storing its review ID in an LMDB database.

    Args:
        cursor: A database cursor for executing SQL queries.
        directory (Path): The base directory path for the LMDB database.
        edit (CaseAttributeEdit): A dataclass containing the edit details, including
            inbredset_id, status, user_id, and changes.

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
        (str(edit.status), edit.user_id,
         json.dumps(edit.changes), str(EditStatus.review),))
    directory = f"{directory}/case-attributes/{edit.inbredset_id}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    env = lmdb.open(directory, map_size=8_000_000)  # 1 MB
    with env.begin(write=True) as txn:
        review_ids = set()
        if reviews := txn.get(b"review"):
            review_ids = pickle.loads(reviews)
        _id = cursor.lastrowid
        review_ids.add(_id)
        txn.put(b"review", pickle.dumps(review_ids))
        return _id


def update_case_attribute(cursor, directory: Path,
                          change_id: int, edit: CaseAttributeEdit) -> bool:
    directory = f"{directory}/case-attributes/{edit.inbredset_id}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    env = lmdb.open(directory, map_size=8_000_000)  # 1 MB
    modifications = dict()
    if edit.changes.get("Modifications") and \
       edit.changes.get("Modifications").get("Current"):
        modifications = edit.changes.get("Modifications").get("Current")
    if not modifications:
        env.close()
        return False
    for strain, changes in modifications.items():
        for case_attribute, value in changes.items():
            value = str(value).strip()
            cursor.execute("SELECT Id AS StrainId, Name AS StrainName FROM Strain "
                           "WHERE Name = %s",
                           (strain,))

            strain_id, _ = cursor.fetchone()
            cursor.execute("SELECT CaseAttributeId, Name AS CaseAttributeName "
                           "FROM CaseAttribute WHERE InbredSetId = %s "
                           "AND Name = %s",
                           (edit.inbredset_id, case_attribute,))
            case_attr_id, _ = cursor.fetchone()
            cursor.execute(
                "INSERT INTO CaseAttributeXRefNew"
                "(InbredSetId, StrainId, CaseAttributeId, Value) "
                "VALUES (%s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE Value=VALUES(value)",
                (edit.inbredset_id, strain_id, case_attr_id, value,))
            cursor.execute(
                "UPDATE caseattributes_audit SET "
                "status = %s WHERE id = %s",
                (str(edit.status), change_id,))
            with env.begin(write=True) as txn:
                review_ids, approved_ids = set(), set()
                if reviews := txn.get(b"review"):
                    review_ids = pickle.loads(reviews)
                if approvals := txn.get(b"approved"):
                    approved_ids = pickle.loads(approvals)
                review_ids.remove(change_id)
                approved_ids.add(change_id)
                txn.put(b"review", pickle.dumps(review_ids))
                txn.put(b"approved", pickle.dumps(approved_ids))
    return True


def __fetch_case_attrs_changes__(cursor, change_ids: tuple) -> list:
    placeholders = ','.join(['%s'] * len(change_ids))
    cursor.execute(
        "SELECT editor, json_diff_data, time_stamp "
        f"FROM caseattributes_audit WHERE id IN ({placeholders})"
        "ORDER BY time_stamp DESC",
        change_ids
    )
    results = cursor.fetchall()
    for el in results:
        el["json_diff_data"] = json.loads(el["json_diff_data"])
    return results


def view_change(cursor, change_id: int) -> dict:
    cursor.execute(
        "SELECT json_diff_data "
        "FROM caseattributes_audit "
        "WHERE id = %s",
        (change_id,)
    )
    json_diff_data, _ = cursor.fetchone()
    if json_diff_data:
        json_diff_data = json.loads(json_diff_data)
        return json_diff_data
    return {}


def get_changes(cursor, inbredset_id: int, directory: Path) -> dict:
    directory = f"{directory}/case-attributes/{inbredset_id}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    review_ids, approved_ids, rejected_ids = set(), set(), set()
    env = lmdb.open(directory, map_size=8_000_000)  # 1 MB
    with env.begin(write=False) as txn:
        if reviews := txn.get(b"review"):
            review_ids = pickle.loads(reviews)
        if approvals := txn.get(b"approved"):
            approved_ids = pickle.loads(approvals)
        if rejections := txn.get(b"rejected"):
            rejected_ids = pickle.loads(rejections)
    reviews, approvals, rejections = {}, {}, {}
    if review_ids:
        reviews = dict(zip(review_ids,
                           __fetch_case_attrs_changes__(cursor, tuple(review_ids))))
    if approved_ids:
        approvals = dict(zip(approved_ids,
                             __fetch_case_attrs_changes__(cursor, tuple(approved_ids))))
    if rejected_ids:
        rejections = dict(zip(rejected_ids,
                              __fetch_case_attrs_changes__(cursor, tuple(rejected_ids))))
    return {
        "reviews": reviews,
        "approvals": approvals,
        "rejections": rejections
    }
