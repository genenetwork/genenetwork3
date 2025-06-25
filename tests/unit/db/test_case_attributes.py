"""Test cases for gn3.db.case_attributes.py"""

import pytest
import tempfile
import os
from pytest_mock import MockFixture
from gn3.db.case_attributes import queue_edit
from gn3.db.case_attributes import (
    CaseAttributeEdit,
    EditStatus
)


@pytest.mark.unit_test
def test_queue_edit(mocker: MockFixture) -> None:
    mock_conn = mocker.MagicMock()
    with mock_conn.cursor() as cursor:
        type(cursor).lastrowid = 28
        TMPDIR = os.environ.get("TMPDIR", tempfile.gettempdir())
        caseattr_id = queue_edit(
            cursor,
            status=EditStatus.review
            directory=TMPDIR,
            edit=CaseAttributeEdit(inbredset_id=1, user_id="xxxx", changes={"a": 1, "b": 2}))
        cursor.execute.assert_called_once_with(
            "INSERT INTO "
            "caseattributes_audit(status, editor, json_diff_data) "
            "VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE status=%s",
            ('review', 'xxxx', '{"a": 1, "b": 2}', 'review'))
        assert 28 == caseattr_id
