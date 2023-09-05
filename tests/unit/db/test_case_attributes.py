"""Test cases for gn3.db.case_attributes.py"""

import pytest
from pytest_mock import MockFixture
from gn3.db.case_attributes import get_unreviewed_diffs
from gn3.db.case_attributes import get_case_attributes
from gn3.db.case_attributes import insert_case_attribute_audit
from gn3.db.case_attributes import approve_case_attribute
from gn3.db.case_attributes import reject_case_attribute


@pytest.mark.unit_test
def test_get_case_attributes(mocker: MockFixture) -> None:
    """Test that all the case attributes are fetched correctly"""
    mock_conn = mocker.MagicMock()
    with mock_conn.cursor() as cursor:
        cursor.fetchall.return_value = (
            (1, "Condition", None),
            (2, "Tissue", None),
            (3, "Age", "Cum sociis natoque penatibus et magnis dis"),
            (4, "Condition", "Description A"),
            (5, "Condition", "Description B"),
        )
        results = get_case_attributes(mock_conn)
        cursor.execute.assert_called_once_with(
            "SELECT Id, Name, Description FROM CaseAttribute"
        )
        assert results == (
            (1, "Condition", None),
            (2, "Tissue", None),
            (3, "Age", "Cum sociis natoque penatibus et magnis dis"),
            (4, "Condition", "Description A"),
            (5, "Condition", "Description B"),
        )


@pytest.mark.unit_test
def test_get_unreviewed_diffs(mocker: MockFixture) -> None:
    """Test that the correct query is called when fetching unreviewed
    case-attributes diff"""
    mock_conn = mocker.MagicMock()
    with mock_conn.cursor() as cursor:
        _ = get_unreviewed_diffs(mock_conn)
        cursor.fetchall.return_value = ((1, "editor", "diff_data_1"),)
        cursor.execute.assert_called_once_with(
            "SELECT id, editor, json_diff_data FROM "
            "caseattributes_audit WHERE status = 'review'"
        )


@pytest.mark.unit_test
def test_insert_case_attribute_audit(mocker: MockFixture) -> None:
    """Test that the updating case attributes uses the correct query"""
    mock_conn = mocker.MagicMock()
    with mock_conn.cursor() as cursor:
        _ = insert_case_attribute_audit(
            mock_conn, status="review", author="Author", data="diff_data"
        )
        cursor.execute.assert_called_once_with(
            "INSERT INTO caseattributes_audit "
            "(status, editor, json_diff_data) "
            "VALUES (%s, %s, %s)",
            ("review", "Author", "diff_data"),
        )


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
