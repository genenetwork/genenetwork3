"""Tests for db/phenotypes.py"""
import json
from unittest import TestCase
from unittest import mock

import pytest

from gn3.db import insert
from gn3.db.metadata_audit import MetadataAudit


class TestMetadatAudit(TestCase):
    """Test cases for fetching chromosomes"""

    @pytest.mark.unit_test
    def test_insert_into_metadata_audit(self):
        """Test that data is inserted correctly in the audit table

        """
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            type(cursor).rowcount = 1
            self.assertEqual(insert(
                conn=db_mock, table="metadata_audit",
                data=MetadataAudit(dataset_id=35,
                                   editor="Bonface",
                                   json_data=json.dumps({"a": "b"}))), 1)
            cursor.execute.assert_called_once_with(
                "INSERT INTO metadata_audit (dataset_id, "
                "editor, json_diff_data) VALUES (%s, %s, %s)",
                (35, 'Bonface', '{"a": "b"}'))
