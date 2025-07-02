"""Module that contains functions for editing case-attribute data"""
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from enum import Enum, auto

import json
import pickle
import lmdb


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
        - inbredset_id (int): The ID of the inbred set associated with
        the edit.
        - status: (EditStatus): The status of this edit.
        - user_id (str): The ID of the user performing the edit.
        - changes (dict): A dictionary containing the changes to be
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
    """
    cursor.execute(
        "INSERT INTO "
        "caseattributes_audit(status, editor, json_diff_data) "
        "VALUES (%s, %s, %s) "
        "ON DUPLICATE KEY UPDATE status=%s",
        (str(edit.status), edit.user_id,
         json.dumps(edit.changes), str(EditStatus.review),))
    directory.mkdir(parents=True, exist_ok=True)
    env = lmdb.open(directory.as_posix(), map_size=8_000_000)  # 1 MB
    with env.begin(write=True) as txn:
        review_ids = set()
        if reviews := txn.get(b"review"):
            review_ids = pickle.loads(reviews)
        _id = cursor.lastrowid
        review_ids.add(_id)
        txn.put(b"review", pickle.dumps(review_ids))
        return _id


def __fetch_case_attrs_changes__(cursor, change_ids: tuple) -> list:
    """Fetches case attribute change records from the audit table for
    given change IDs.

    Retrieves records from the `caseattributes_audit` table for the
    specified `change_ids`, including the editor, JSON diff data, and
    timestamp. The JSON diff data is deserialized into a Python
    dictionary for each record. Results are ordered by timestamp in
    descending order (most recent first).

    Args:
        cursor: A MySQLdb cursor for executing SQL queries.
        change_ids (tuple): A tuple of integers representing the IDs
        of changes to fetch.

    Returns:
        list: A list of dictionaries, each containing the `editor`,
            `json_diff_data` (as a deserialized dictionary), and `time_stamp`
            for the matching change IDs. Returns an empty list if no records
            are found.

    Notes:
        - The function assumes `change_ids` is a non-empty tuple of valid integers.
        - The `json_diff_data` column in `caseattributes_audit` is expected to contain valid
          JSON strings, which are deserialized into dictionaries.
        - The query uses parameterized placeholders to prevent SQL injection.
        - This is an internal helper function (indicated by double underscores) used by
          other functions like `get_changes`.

    Raises:
        json.JSONDecodeError: If any `json_diff_data` value cannot be deserialized.
        TypeError: If `change_ids` is empty or contains non-integer values, potentially
            causing a database error.

    """
    if not change_ids:
        return {}  # type:ignore
    placeholders = ','.join(['%s'] * len(change_ids))
    cursor.execute(
        "SELECT editor, json_diff_data, time_stamp "
        f"FROM caseattributes_audit WHERE id IN ({placeholders}) "
        "ORDER BY time_stamp DESC",
        change_ids
    )
    results = cursor.fetchall()
    for el in results:
        el["json_diff_data"] = json.loads(el["json_diff_data"])
    return results


def view_change(cursor, change_id: int) -> dict:
    """Queries the `caseattributes_audit` table to fetch the
    `json_diff_data` column for the given `change_id`. The JSON data
    is deserialized into a Python dictionary and returned.  If no
    record is found or the `json_diff_data` is None, an empty
    dictionary is returned.

    Args:
        cursor: A MySQLdb cursor for executing SQL queries.
        change_id (int): The ID of the change to retrieve from the
        `caseattributes_audit` table.

    Returns:
        dict: The deserialized JSON diff data as a dictionary if the
              record exists and contains valid JSON; otherwise, an
              empty dictionary.

    Raises:
        json.JSONDecodeError: If the `json_diff_data` cannot be
            deserialized due to invalid JSON.
        TypeError: If `cursor.fetchone()` returns None (e.g., no
            record found) and `json_diff_data` is accessed, though the
            function handles this by returning an empty dictionary.

    """
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


def get_changes(cursor, change_type: EditStatus, directory: Path) -> dict:
    """Retrieves case attribute changes for given lmdb data in
    directory categorized by review status.

    Fetches change IDs from an LMDB database, categorized into the
    "data" key based on the EditStatus

    Args:
        - cursor: A MySQLdb cursor for executing SQL queries.
        - change_type (EditStatus): The status of changes to retrieve
          ('review', 'approved', or 'rejected').
        - directory (Path): The base directory path for the LMDB
          database.

    Returns:
        dict: A dictionary with two keys:
            -'count': A dictionary with counts of 'reviews',
                    'approvals' and 'rejections'.
            - 'data': contains the json diff data of the modified data

    Raises:
        json.JSONDecodeError: If any `json_diff_data` in the audit
            table cannot be deserialized by
            `__fetch_case_attrs_changes__`.
        TypeError: If `inbredset_id` is not an integer or if LMDB data
            cannot be deserialized.  Also raised when an invalid change_id
            is used.

    """
    directory.mkdir(parents=True, exist_ok=True)
    review_ids, approved_ids, rejected_ids = set(), set(), set()
    directory.mkdir(parents=True, exist_ok=True)
    env = lmdb.open(directory.as_posix(), map_size=8_000_000)  # 1 MB
    with env.begin(write=False) as txn:
        if reviews := txn.get(b"review"):
            review_ids = pickle.loads(reviews)
        if approvals := txn.get(b"approved"):
            approved_ids = pickle.loads(approvals)
        if rejections := txn.get(b"rejected"):
            rejected_ids = pickle.loads(rejections)
    changes = {}
    match change_type:
        case EditStatus.review:
            changes = dict(
                zip(review_ids,
                    __fetch_case_attrs_changes__(cursor, tuple(review_ids)))
            )
        case EditStatus.approved:
            changes = dict(
                zip(approved_ids,
                    __fetch_case_attrs_changes__(cursor, tuple(approved_ids)))
            )
        case EditStatus.rejected:
            changes = dict(zip(rejected_ids,
                               __fetch_case_attrs_changes__(cursor, tuple(rejected_ids))))
        case _:
            raise TypeError
    return {
        "change-type": str(change_type),
        "count": {
            "reviews": len(review_ids),
            "approvals": len(approved_ids),
            "rejections": len(rejected_ids)
        },
        "data": changes
    }


# pylint: disable=[too-many-locals]
def apply_change(cursor, change_type: EditStatus, change_id: int, directory: Path) -> bool:
    """Applies or rejects a case attribute change and updates its
    status in the audit table and LMDB.

    Processes a change identified by `change_id` based on the
    specified `change_type` (approved or rejected). For approved
    changes, applies modifications to the `CaseAttributeXRefNew` table
    using bulk inserts and updates the audit status. For rejected
    changes, updates the audit status only.  Manages change IDs in
    LMDB by moving them from the 'review' set to either 'approved' or
    'rejected' sets. Returns False if the `change_id` is not in the
    review set.

    Args:
        cursor: A MySQLdb cursor for executing SQL queries.
        change_type (EditStatus): The action to perform, either
            `EditStatus.approved` or `EditStatus.rejected`.
        change_id (int): The ID of the change to process,
            corresponding to a record in `caseattributes_audit`.
        directory (Path): The base directory path for the LMDB
        database.

    Returns:
        bool: True if the change was successfully applied or rejected,
            False if `change_id` is not found in the LMDB 'review'
            set.

    Notes:
        - Opens an LMDB environment in the specified `directory` with
          a map size of 8 MB.
        - For `EditStatus.approved`, fetches `json_diff_data` from
          `caseattributes_audit`, extracts modifications, and performs
          bulk inserts into `CaseAttributeXRefNew` with `ON DUPLICATE
          KEY UPDATE`.
        - For `EditStatus.rejected`, updates the
          `caseattributes_audit` status without modifying case
          attributes.
        - Uses bulk `SELECT` queries to fetch `StrainId` and
          `CaseAttributeId` values efficiently.
        - Assumes `CaseAttributeXRefNew` has a unique key on
          `(InbredSetId, StrainId, CaseAttributeId)` for `ON DUPLICATE
          KEY UPDATE`.
        - The `json_diff_data` is expected to contain valid JSON with
          an `inbredset_id` and `Modifications.Current` structure.
        - The second column from `fetchone()` is ignored (denoted by
          `_`).

    Raises:
        ValueError: If `change_type` is neither `EditStatus.approved`
            nor `EditStatus.rejected`.
        json.JSONDecodeError: If `json_diff_data` cannot be
            deserialized for approved changes.
        TypeError: If `cursor.fetchone()` returns None for
            `json_diff_data` or if `strain_id` or `caseattr_id` are
            missing during bulk insert preparation.
        pickle.UnpicklingError: If LMDB data (e.g., 'review' or
            'approved' sets) cannot be deserialized.

    """
    review_ids, approved_ids, rejected_ids = set(), set(), set()
    directory.mkdir(parents=True, exist_ok=True)
    env = lmdb.open(directory.as_posix(), map_size=8_000_000)  # 1 MB
    with env.begin(write=True) as txn:
        if reviews := txn.get(b"review"):
            review_ids = pickle.loads(reviews)
        if change_id not in review_ids:
            return False
        match change_type:
            case EditStatus.rejected:
                cursor.execute(
                    "UPDATE caseattributes_audit "
                    "SET status = %s "
                    "WHERE id = %s",
                    (str(change_type), change_id))
                review_ids.discard(change_id)
                rejected_ids.add(change_id)
                txn.put(b"review", pickle.dumps(review_ids))
                txn.put(b"rejected", pickle.dumps(rejected_ids))
                return True
            case EditStatus.approved:
                cursor.execute(
                    "SELECT json_diff_data "
                    "FROM caseattributes_audit WHERE "
                    "id = %s",
                    (change_id,)
                )
                json_diff_data, _ = cursor.fetchone()
                json_diff_data = json.loads(json_diff_data)
                inbredset_id = json_diff_data.get("inbredset_id")
                modifications = json_diff_data.get(
                    "Modifications", {}).get("Current", {})
                strains = tuple(modifications.keys())
                case_attrs = set()
                for data in modifications.values():
                    case_attrs.update(data.keys())

                # Bulk fetch strain ids
                strain_id_map = {}
                if strains:
                    cursor.execute(
                        "SELECT Name, Id FROM Strain WHERE Name IN "
                        f"({', '.join(['%s'] * len(strains))})",
                        strains
                    )
                    for name, strain_id in cursor.fetchall():
                        strain_id_map[name] = strain_id

                # Bulk fetch case attr ids
                caseattr_id_map = {}
                if case_attrs:
                    cursor.execute(
                        "SELECT Name, CaseAttributeId FROM CaseAttribute "
                        "WHERE InbredSetId = %s AND Name IN "
                        f"({', '.join(['%s'] * len(case_attrs))})",
                        (inbredset_id, *case_attrs)
                    )
                    for name, caseattr_id in cursor.fetchall():
                        caseattr_id_map[name] = caseattr_id

                # Bulk insert data
                insert_data = []
                for strain, data in modifications.items():
                    strain_id = strain_id_map.get(strain)
                    for case_attr, value in data.items():
                        insert_data.append({
                            "inbredset_id": inbredset_id,
                            "strain_id": strain_id,
                            "caseattr_id": caseattr_id_map.get(case_attr),
                            "value": value,
                        })
                if insert_data:
                    cursor.executemany(
                        "INSERT INTO CaseAttributeXRefNew "
                        "(InbredSetId, StrainId, CaseAttributeId, Value) "
                        "VALUES (%(inbredset_id)s, %(strain_id)s, %(caseattr_id)s, %(value)s) "
                        "ON DUPLICATE KEY UPDATE Value = VALUES(Value)",
                        insert_data
                    )

                # Update LMDB and audit table
                cursor.execute(
                    "UPDATE caseattributes_audit "
                    "SET status = %s "
                    "WHERE id = %s",
                    (str(change_type), change_id))
                if approvals := txn.get(b"approved"):
                    approved_ids = pickle.loads(approvals)
                    review_ids.discard(change_id)
                    approved_ids.add(change_id)
                    txn.put(b"review", pickle.dumps(review_ids))
                    txn.put(b"approvals", pickle.dumps(approved_ids))
                return True
            case _:
                raise ValueError
