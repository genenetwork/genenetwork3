"""Test cases for gn3.db.case_attributes.py"""

import pytest
import tempfile
import os
from pytest_mock import MockFixture
from gn3.db.case_attributes import queue_edit
from gn3.db.case_attributes import CaseAttributeEdit
from gn3.db.case_attributes import approve_case_attribute
from gn3.db.case_attributes import reject_case_attribute


@pytest.mark.unit_test
def test_queue_edit(mocker: MockFixture) -> None:
    mock_conn = mocker.MagicMock()
    with mock_conn.cursor() as cursor:
        type(cursor).lastrowid = 28
        TMPDIR = os.environ.get("TMPDIR", tempfile.gettempdir())
        review_ids = queue_edit(
            cursor,
            directory=TMPDIR,
            edit=CaseAttributeEdit(inbredset_id=1, user_id="xxxx", changes={"a": 1, "b": 2}))
        cursor.execute.assert_called_once_with(
            "INSERT INTO "
            "caseattributes_audit(status, editor, json_diff_data) "
            "VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE status=%s",
            ('review', 'xxxx', '{"a": 1, "b": 2}', 'review'))
        assert {28} == review_ids


@pytest.mark.unit_test
def test_reject_case_attribute(mocker: MockFixture) -> None:
    """Test rejecting a case-attribute"""
    mock_conn = mocker.MagicMock()
    with mock_conn.cursor() as cursor:
        _ = reject_case_attribute(
            mock_conn,
            case_attr_audit_id=1,
        )
        cursor.execute.assert_called_once_with(
            "UPDATE caseattributes_audit SET "
            "status = 'rejected' WHERE id = %s",
            (1,),
        )


@pytest.mark.unit_test
def test_approve_inserting_case_attribute(mocker: MockFixture) -> None:
    """Test approving inserting a case-attribute"""
    mock_conn = mocker.MagicMock()
    with mock_conn.cursor() as cursor:
        type(cursor).rowcount = 1
        cursor.fetchone.return_value = (
            """
        {"Insert": {"name": "test", "description": "Random Description"}}
        """,
        )
        _ = approve_case_attribute(
            mock_conn,
            case_attr_audit_id=3,
        )
        calls = [
            mocker.call(
                "SELECT json_diff_data FROM caseattributes_audit "
                "WHERE id = %s",
                (3,),
            ),
            mocker.call(
                "INSERT INTO CaseAttribute "
                "(Name, Description) VALUES "
                "(%s, %s)",
                (
                    "test",
                    "Random Description",
                ),
            ),
            mocker.call(
                "UPDATE caseattributes_audit SET "
                "status = 'approved' WHERE id = %s",
                (3,),
            ),
        ]
        cursor.execute.assert_has_calls(calls, any_order=False)


@pytest.mark.unit_test
def test_approve_deleting_case_attribute(mocker: MockFixture) -> None:
    """Test deleting a case-attribute"""
    mock_conn = mocker.MagicMock()
    with mock_conn.cursor() as cursor:
        type(cursor).rowcount = 1
        cursor.fetchone.return_value = (
            """
        {"Deletion": {"id": "12", "name": "test", "description": ""}}
        """,
        )
        _ = approve_case_attribute(
            mock_conn,
            case_attr_audit_id=3,
        )
        calls = [
            mocker.call(
                "SELECT json_diff_data FROM caseattributes_audit "
                "WHERE id = %s",
                (3,),
            ),
            mocker.call("DELETE FROM CaseAttribute WHERE Id = %s", ("12",)),
            mocker.call(
                "UPDATE caseattributes_audit SET "
                "status = 'approved' WHERE id = %s",
                (3,),
            ),
        ]
        cursor.execute.assert_has_calls(calls, any_order=False)


@pytest.mark.unit_test
def test_approve_modifying_case_attribute(mocker: MockFixture) -> None:
    """Test modifying a case-attribute"""
    mock_conn = mocker.MagicMock()
    with mock_conn.cursor() as cursor:
        type(cursor).rowcount = 1
        cursor.fetchone.return_value = (
            """
{
  "id": "12",
  "Modification": {
    "description": {
      "Current": "Test",
      "Original": "A"
    },
    "name": {
      "Current": "Height (A)",
      "Original": "Height"
    }
  }
}""",
        )
        _ = approve_case_attribute(
            mock_conn,
            case_attr_audit_id=3,
        )
        calls = [
            mocker.call(
                "SELECT json_diff_data FROM caseattributes_audit "
                "WHERE id = %s",
                (3,),
            ),
            mocker.call(
                "UPDATE CaseAttribute SET Description = %s WHERE Id = %s",
                (
                    "Test",
                    "12",
                ),
            ),
            mocker.call(
                "UPDATE CaseAttribute SET Name = %s WHERE Id = %s",
                (
                    "Height (A)",
                    "12",
                ),
            ),
            mocker.call(
                "UPDATE caseattributes_audit SET "
                "status = 'approved' WHERE id = %s",
                (3,),
            ),
        ]
        cursor.execute.assert_has_calls(calls, any_order=False)
