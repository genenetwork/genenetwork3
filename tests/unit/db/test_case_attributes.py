"""Test cases for gn3.db.case_attributes.py"""

import pytest
import pickle
import tempfile
import os
import json
from pathlib import Path
from pytest_mock import MockFixture
from gn3.db.case_attributes import queue_edit
from gn3.db.case_attributes import (
    CaseAttributeEdit,
    EditStatus,
    apply_change,
    view_change,
    update_case_attribute
)


@pytest.mark.unit_test
def test_queue_edit(mocker: MockFixture) -> None:
    mock_conn = mocker.MagicMock()
    with mock_conn.cursor() as cursor:
        type(cursor).lastrowid = 28
        TMPDIR = os.environ.get("TMPDIR", tempfile.gettempdir())
        caseattr_id = queue_edit(
            cursor,
            directory=TMPDIR,
            edit=CaseAttributeEdit(
                inbredset_id=1, status=EditStatus.review,
                user_id="xxxx", changes={"a": 1, "b": 2}
            ))
        cursor.execute.assert_called_once_with(
            "INSERT INTO "
            "caseattributes_audit(status, editor, json_diff_data) "
            "VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE status=%s",
            ('review', 'xxxx', '{"a": 1, "b": 2}', 'review'))
        assert 28 == caseattr_id


@pytest.mark.unit_test
def test_update_case_attribute_success(mocker: MockFixture) -> None:
    """Test successful case attribute update with valid modifications."""
    mock_cursor, mock_conn = mocker.MagicMock(), mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_lmdb = mocker.patch("gn3.db.case_attributes.lmdb")
    mock_env, mock_txn = mocker.MagicMock(), mocker.MagicMock()
    mock_lmdb.open.return_value = mock_env
    mock_env.begin.return_value.__enter__.return_value = mock_txn
    mock_txn.get.side_effect = [
        pickle.dumps({100}),  # b"review" key
        None,                 # b"approved" key
    ]

    TMPDIR = Path(os.environ.get("TMPDIR", tempfile.gettempdir()))
    edit = CaseAttributeEdit(
        inbredset_id=1,
        user_id="test_user",
        status=EditStatus.approved,
        changes={
            "Modifications": {
                "Current": {
                    "Strain1": {"Attribute1": "Value1"}
                }
            }
        }
    )
    change_id = 100

    # Mock cursor fetch results
    mock_cursor.fetchone.side_effect = [
        (10, "Strain1"),          # Strain query
        (20, "Attribute1"),       # CaseAttribute query
    ]

    assert update_case_attribute(mock_cursor, TMPDIR, change_id, edit)

    # Assertions for lmdb interactions
    mock_lmdb.open.assert_called_once_with(
        f"{TMPDIR}/case-attributes/1", map_size=8_000_000)
    mock_env.begin.assert_called_once_with(write=True)
    mock_txn.get.assert_has_calls([
        mocker.call(b"review"),
        mocker.call(b"approved")
    ])
    mock_txn.put.assert_has_calls([
        mocker.call(b"review", pickle.dumps(set())),
        mocker.call(b"approved", pickle.dumps({100}))
    ])

    # Assertions for SQL executions
    mock_cursor.execute.assert_has_calls([
        mocker.call(
            "SELECT Id AS StrainId, Name AS StrainName FROM Strain WHERE Name = %s",
            ("Strain1",)
        ),
        mocker.call(
            "SELECT CaseAttributeId, Name AS CaseAttributeName FROM CaseAttribute "
            "WHERE InbredSetId = %s AND Name = %s",
            (1, "Attribute1")
        ),
        mocker.call(
            "INSERT INTO CaseAttributeXRefNew(InbredSetId, StrainId, CaseAttributeId, Value) "
            "VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE Value=VALUES(value)",
            (1, 10, 20, "Value1")
        ),
        mocker.call(
            "UPDATE caseattributes_audit SET status = %s WHERE id = %s",
            ("approved", 100)
        )
    ])


@pytest.mark.unit_test
def test_update_case_attribute_no_modifications(mocker: MockFixture) -> None:
    """Test update_case_attribute with no modifications in edit.changes."""
    mock_cursor, mock_conn = mocker.MagicMock(), mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_lmdb = mocker.patch("gn3.db.case_attributes.lmdb")
    mock_env, mock_txn = mocker.MagicMock(), mocker.MagicMock()
    TMPDIR = Path(os.environ.get("TMPDIR", tempfile.gettempdir()))
    edit = CaseAttributeEdit(
        inbredset_id=1,
        user_id="test_user",
        status=EditStatus.approved,
        changes={}  # No modifications
    )
    change_id = 28
    assert not update_case_attribute(mock_cursor, TMPDIR, change_id, edit)


@pytest.mark.unit_test
def test_view_change(mocker: MockFixture) -> None:
    """Test view_change function."""
    sample_json_diff = {
        "inbredset_id": 1,
        "Modifications": {
            "Original": {
                "B6D2F1": {"Epoch": "10au"},
                "BXD100": {"Epoch": "3b"},
                "BXD101": {"SeqCvge": "29"},
                "BXD102": {"Epoch": "3b"},
                "BXD108": {"SeqCvge": ""}
            },
            "Current": {
                "B6D2F1": {"Epoch": "10"},
                "BXD100": {"Epoch": "3"},
                "BXD101": {"SeqCvge": "2"},
                "BXD102": {"Epoch": "3"},
                "BXD108": {"SeqCvge": "oo"}
            }
        }
    }
    CHANGE_ID = 28
    mock_cursor, mock_conn = mocker.MagicMock(), mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (json.dumps(sample_json_diff), None)
    assert view_change(mock_cursor, CHANGE_ID) == sample_json_diff
    mock_cursor.execute.assert_called_once_with(
        "SELECT json_diff_data FROM caseattributes_audit WHERE id = %s",
        (CHANGE_ID,))
    mock_cursor.fetchone.assert_called_once()


@pytest.mark.unit_test
def test_view_change_invalid_json(mocker: MockFixture) -> None:
    """Test invalid json when view_change is called"""
    CHANGE_ID = 28
    mock_cursor, mock_conn = mocker.MagicMock(), mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = ("invalid_json_string", None)
    with pytest.raises(json.JSONDecodeError):
        view_change(mock_cursor, CHANGE_ID)
    mock_cursor.execute.assert_called_once_with(
        "SELECT json_diff_data FROM caseattributes_audit WHERE id = %s",
        (CHANGE_ID,))


@pytest.mark.unit_test
def test_view_change_no_data(mocker: MockFixture) -> None:
    "Test no result when view_change is called"
    CHANGE_ID = 28
    mock_cursor, mock_conn = mocker.MagicMock(), mocker.MagicMock()
    mock_cursor.fetchone.return_value = (None, None)
    assert view_change(mock_cursor, CHANGE_ID) == {}
    mock_cursor.execute.assert_called_once_with(
        "SELECT json_diff_data FROM caseattributes_audit WHERE id = %s",
        (CHANGE_ID,))


@pytest.mark.unit_test
def test_apply_change_approved(mocker: MockFixture) -> None:
    """Test approving a change"""
    mock_cursor, mock_conn = mocker.MagicMock(), mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_lmdb = mocker.patch("gn3.db.case_attributes.lmdb")
    mock_env, mock_txn = mocker.MagicMock(), mocker.MagicMock()
    mock_lmdb.open.return_value = mock_env
    mock_env.begin.return_value.__enter__.return_value = mock_txn
    CHANGE_ID, review_ids = 1, {1, 2, 3}
    mock_txn.get.side_effect = (
        pickle.dumps(review_ids),  # b"review" key
        None,                      # b"approved" key
    )
    TMPDIR = Path(os.environ.get("TMPDIR", tempfile.gettempdir()))
    mock_cursor.fetchone.return_value = (json.dumps({
        "inbredset_id": 1,
        "Modifications": {
            "Current": {
                "B6D2F1": {"Epoch": "10"},
                "BXD100": {"Epoch": "3"},
                "BXD101": {"SeqCvge": "2"},
                "BXD102": {"Epoch": "3"},
                "BXD108": {"SeqCvge": "oo"}
            }
        }
    }), None)
    mock_cursor.fetchall.side_effect = [
        [  # Strain query
            ("B6D2F1", 1), ("BXD100", 2),
            ("BXD101", 3), ("BXD102", 4),
            ("BXD108", 5)],
        [  # CaseAttribute query
            ("Epoch", 101), ("SeqCvge", 102)]
    ]
    assert apply_change(mock_cursor, EditStatus.approved,
                        CHANGE_ID, TMPDIR) is True
    assert mock_cursor.execute.call_count == 4
    mock_cursor.execute.assert_has_calls([
        mocker.call(
            "SELECT json_diff_data FROM caseattributes_audit WHERE id = %s",
            (CHANGE_ID,)),
        mocker.call(
            "SELECT Name, Id FROM Strain WHERE Name IN (%s, %s, %s, %s, %s)",
            ("B6D2F1", "BXD100", "BXD101", "BXD102", "BXD108")),
        mocker.call(
            "SELECT Name, CaseAttributeId FROM CaseAttribute WHERE InbredSetId = %s AND Name IN (%s, %s)",
            (1, "SeqCvge", "Epoch")),
        mocker.call(
            "UPDATE caseattributes_audit SET status = %s WHERE id = %s",
            ("approved", CHANGE_ID))
    ])
    mock_cursor.executemany.assert_called_once_with(
        "INSERT INTO CaseAttributeXRefNew (InbredSetId, StrainId, CaseAttributeId, Value) "
        "VALUES (%(inbredset_id)s, %(strain_id)s, %(caseattr_id)s, %(value)s) "
        "ON DUPLICATE KEY UPDATE Value = VALUES(Value)",
        [
            {"inbredset_id": 1, "strain_id": 1, "caseattr_id": 101, "value": "10"},
            {"inbredset_id": 1, "strain_id": 2, "caseattr_id": 101, "value": "3"},
            {"inbredset_id": 1, "strain_id": 3, "caseattr_id": 102, "value": "2"},
            {"inbredset_id": 1, "strain_id": 4, "caseattr_id": 101, "value": "3"},
            {"inbredset_id": 1, "strain_id": 5, "caseattr_id": 102, "value": "oo"}
        ]
    )


@pytest.mark.unit_test
def test_apply_change_rejected(mocker: MockFixture) -> None:
    """Test rejecting a change"""
    mock_cursor, mock_conn = mocker.MagicMock(), mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_lmdb = mocker.patch("gn3.db.case_attributes.lmdb")
    mock_env, mock_txn = mocker.MagicMock(), mocker.MagicMock()
    mock_lmdb.open.return_value = mock_env
    mock_env.begin.return_value.__enter__.return_value = mock_txn
    TMPDIR = Path(os.environ.get("TMPDIR", tempfile.gettempdir()))
    CHANGE_ID, review_ids = 3, {1, 2, 3}
    mock_txn.get.side_effect = [
        pickle.dumps(review_ids),  # review_ids
        None  # rejected_ids (initially empty)
    ]

    assert apply_change(mock_cursor, EditStatus.rejected,
                        CHANGE_ID, TMPDIR) is True

    # Verify SQL query call sequence
    mock_cursor.execute.assert_called_once_with(
        "UPDATE caseattributes_audit SET status = %s WHERE id = %s",
        (str(EditStatus.rejected), CHANGE_ID))
    mock_cursor.executemany.assert_not_called()

    # Verify LMDB operations
    mock_env.begin.assert_called_once_with(write=True)
    expected_txn_calls = [
        mocker.call(b"review", pickle.dumps({1, 2})),
        mocker.call(b"rejected", pickle.dumps({3}))
    ]
    mock_txn.put.assert_has_calls(expected_txn_calls, any_order=False)


@pytest.mark.unit_test
def test_apply_change_non_existent_change_id(mocker: MockFixture) -> None:
    """Test that there's a missing change_id from the returned LMDB rejected set."""
    mock_env, mock_txn = mocker.MagicMock(), mocker.MagicMock()
    mock_cursor, mock_conn = mocker.MagicMock(), mocker.MagicMock()
    mock_lmdb = mocker.patch("gn3.db.case_attributes.lmdb")
    mock_lmdb.open.return_value = mock_env
    mock_conn.cursor.return_value = mock_cursor
    mock_env.begin.return_value.__enter__.return_value = mock_txn
    CHANGE_ID, review_ids = 28, {1, 2, 3}
    mock_txn.get.side_effect = [
        pickle.dumps(review_ids),  # b"review" key
        None,                      # b"approved" key
    ]
    TMPDIR = Path(os.environ.get("TMPDIR", tempfile.gettempdir()))
    assert apply_change(mock_cursor, EditStatus.approved,
                        CHANGE_ID, TMPDIR) is False
