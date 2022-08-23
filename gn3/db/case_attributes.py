"""Module that contains functions for editing case-attribute data"""
from typing import Any, Optional, Tuple

import json
import MySQLdb


def get_case_attributes(conn) -> Optional[Tuple]:
    """Get all the case attributes from the database."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT Id, Name, Description FROM CaseAttribute")
        return cursor.fetchall()


def get_unreviewed_diffs(conn: Any) -> Optional[tuple]:
    """Fetch all case attributes in GN"""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id, editor, json_diff_data FROM "
            "caseattributes_audit WHERE status = 'review'"
        )
        return cursor.fetchall()


def insert_case_attribute_audit(
    conn: Any, status: str, author: str, data: str
) -> int:
    """Update the case_attribute_audit table"""
    rowcount = 0
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO caseattributes_audit "
                "(status, editor, json_diff_data) "
                "VALUES (%s, %s, %s)",
                (status, author, data,),
            )
            rowcount = cursor.rowcount
    except Exception as _e:
        raise MySQLdb.Error(_e) from _e
    return rowcount


def reject_case_attribute(conn: Any, case_attr_audit_id: int) -> int:
    """Given the id of the json_diff in the case_attribute_audit table, reject
    it"""
    rowcount = 0
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE caseattributes_audit SET "
                "status = 'rejected' WHERE id = %s",
                (case_attr_audit_id,),
            )
            rowcount = cursor.rowcount
    except Exception as _e:
        raise MySQLdb.Error(_e) from _e
    return rowcount


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
                        "DELETE FROM CaseAttribute " "WHERE Id = %s",
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
