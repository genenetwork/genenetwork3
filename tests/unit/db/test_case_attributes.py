"""Test cases for gn3.db.case_attributes.py"""

import pickle
import tempfile
import os
import json
from pathlib import Path
import pytest
from pytest_mock import MockFixture
from gn3.db.case_attributes import queue_edit
from gn3.db.case_attributes import (
    CaseAttributeEdit,
    EditStatus,
    apply_change,
    get_changes,
    view_change
)


@pytest.mark.unit_test
def test_queue_edit(mocker: MockFixture) -> None:
    """Test queueing an edit."""
    mock_conn = mocker.MagicMock()
    with mock_conn.cursor() as cursor:
        type(cursor).lastrowid = 28
        tmpdir = Path(os.environ.get("TMPDIR", tempfile.gettempdir()))
        caseattr_id = queue_edit(
            cursor,
            directory=tmpdir,
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
    change_id = 28
    mock_cursor, mock_conn = mocker.MagicMock(), mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (json.dumps(sample_json_diff), None)
    assert view_change(mock_cursor, change_id) == sample_json_diff
    mock_cursor.execute.assert_called_once_with(
        "SELECT json_diff_data FROM caseattributes_audit WHERE id = %s",
        (change_id,))
    mock_cursor.fetchone.assert_called_once()


@pytest.mark.unit_test
def test_view_change_invalid_json(mocker: MockFixture) -> None:
    """Test invalid json when view_change is called"""
    change_id = 28
    mock_cursor, mock_conn = mocker.MagicMock(), mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = ("invalid_json_string", None)
    with pytest.raises(json.JSONDecodeError):
        view_change(mock_cursor, change_id)
    mock_cursor.execute.assert_called_once_with(
        "SELECT json_diff_data FROM caseattributes_audit WHERE id = %s",
        (change_id,))


@pytest.mark.unit_test
def test_view_change_no_data(mocker: MockFixture) -> None:
    "Test no result when view_change is called"
    change_id = 28
    mock_cursor, mock_conn = mocker.MagicMock(), mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (None, None)
    assert view_change(mock_cursor, change_id) == {}
    mock_cursor.execute.assert_called_once_with(
        "SELECT json_diff_data FROM caseattributes_audit WHERE id = %s",
        (change_id,))


@pytest.mark.unit_test
def test_apply_change_approved(mocker: MockFixture) -> None:
    """Test approving a change"""
    mock_cursor, mock_conn = mocker.MagicMock(), mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_lmdb = mocker.patch("gn3.db.case_attributes.lmdb")
    mock_env, mock_txn = mocker.MagicMock(), mocker.MagicMock()
    mock_lmdb.open.return_value = mock_env
    mock_env.begin.return_value.__enter__.return_value = mock_txn
    change_id, review_ids = 1, {1, 2, 3}
    mock_txn.get.side_effect = (
        pickle.dumps(review_ids),  # b"review" key
        None,                      # b"approved" key
    )
    tmpdir = Path(os.environ.get("TMPDIR", tempfile.gettempdir()))
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
                        change_id, tmpdir) is True
    assert mock_cursor.execute.call_count == 4
    mock_cursor.execute.assert_has_calls([
        mocker.call(
            "SELECT json_diff_data FROM caseattributes_audit WHERE id = %s",
            (change_id,)),
        mocker.call(
            "SELECT Name, Id FROM Strain WHERE Name IN (%s, %s, %s, %s, %s)",
            ("B6D2F1", "BXD100", "BXD101", "BXD102", "BXD108")),
        mocker.call(
            "SELECT Name, CaseAttributeId FROM CaseAttribute "
            "WHERE InbredSetId = %s AND Name IN (%s, %s)",
            (1, "Epoch", "SeqCvge")),
        mocker.call(
            "UPDATE caseattributes_audit SET status = %s WHERE id = %s",
            ("approved", change_id))
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
    tmpdir = Path(os.environ.get("TMPDIR", tempfile.gettempdir()))
    change_id, review_ids = 3, {1, 2, 3}
    mock_txn.get.side_effect = [
        pickle.dumps(review_ids),  # review_ids
        None  # rejected_ids (initially empty)
    ]

    assert apply_change(mock_cursor, EditStatus.rejected,
                        change_id, tmpdir) is True

    # Verify SQL query call sequence
    mock_cursor.execute.assert_called_once_with(
        "UPDATE caseattributes_audit SET status = %s WHERE id = %s",
        (str(EditStatus.rejected), change_id))
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
    change_id, review_ids = 28, {1, 2, 3}
    mock_txn.get.side_effect = [
        pickle.dumps(review_ids),  # b"review" key
        None,                      # b"approved" key
    ]
    tmpdir = Path(os.environ.get("TMPDIR", tempfile.gettempdir()))
    assert apply_change(mock_cursor, EditStatus.approved,
                        change_id, tmpdir) is False


@pytest.mark.unit_test
def test_get_changes(mocker: MockFixture) -> None:
    """Test that reviews are correctly fetched"""
    mock_fetch_case_attrs_changes = mocker.patch(
        "gn3.db.case_attributes.__fetch_case_attrs_changes__"
    )
    mock_fetch_case_attrs_changes.return_value = [
        {
            "editor": "user1",
            "json_diff_data": {
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
            },
            "time_stamp": "2025-07-01 12:00:00"
        },
        {
            "editor": "user2",
            "json_diff_data": {
                "inbredset_id": 1,
                "Modifications": {
                    "Original": {"BXD200": {"Epoch": "5a"}},
                    "Current": {"BXD200": {"Epoch": "5"}}
                }
            },
            "time_stamp": "2025-07-01 12:01:00"
        }
    ]
    mock_lmdb = mocker.patch("gn3.db.case_attributes.lmdb")
    mock_env, mock_txn = mocker.MagicMock(), mocker.MagicMock()
    mock_lmdb.open.return_value = mock_env
    mock_env.begin.return_value.__enter__.return_value = mock_txn
    review_ids, approved_ids, rejected_ids = {1, 4}, {2, 3}, {5, 6, 7, 10}
    mock_txn.get.side_effect = (
        pickle.dumps(review_ids),    # b"review" key
        pickle.dumps(approved_ids),  # b"approved" key
        pickle.dumps(rejected_ids)   # b"rejected" key
    )
    result = get_changes(cursor=mocker.MagicMock(),
                         change_type=EditStatus.review,
                         directory=Path("/tmp"))
    expected = {
        "change-type": "review",
        "count": {
            "reviews": 2,
            "approvals": 2,
            "rejections": 4
        },
        "data": {
            1: {
                "editor": "user1",
                "json_diff_data": {
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
                },
                "time_stamp": "2025-07-01 12:00:00"
            },
            4: {
                'editor': 'user2',
                'json_diff_data': {
                    'inbredset_id': 1,
                    'Modifications': {
                        'Original': {
                            'BXD200': {'Epoch': '5a'}
                        },
                        'Current': {
                            'BXD200': {'Epoch': '5'}
                        }
                    }
                },
                "time_stamp": "2025-07-01 12:01:00"
            }
        }
    }
    assert result == expected
