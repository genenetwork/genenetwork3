"""Tests for db/phenotypes.py"""
from unittest import TestCase
from unittest import mock

import pytest

from gn3.db import fetchall
from gn3.db import fetchone
from gn3.db import update
from gn3.db import diff_from_dict
from gn3.db.probesets import Probeset
from gn3.db.phenotypes import Phenotype
from gn3.db.metadata_audit import MetadataAudit


class TestCrudMethods(TestCase):
    """Test cases for CRUD methods"""

    @pytest.mark.unit_test
    def test_update_phenotype_with_no_data(self):
        """Test that a phenotype is updated correctly if an empty Phenotype dataclass
        is provided

        """
        db_mock = mock.MagicMock()
        self.assertEqual(update(
            conn=db_mock, table="Phenotype",
            data=Phenotype(), where=Phenotype()), None)

    @pytest.mark.unit_test
    def test_update_phenotype_with_data(self):
        """
        Test that a phenotype is updated correctly if some
        data is provided
        """
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            type(cursor).rowcount = 1
            self.assertEqual(update(
                conn=db_mock, table="Phenotype",
                data=Phenotype(
                    pre_pub_description="Test Pre Pub",
                    submitter="Rob",
                    post_pub_description="Test Post Pub"),
                where=Phenotype(id_=1, owner="Rob")), 1)
            cursor.execute.assert_called_once_with(
                "UPDATE Phenotype SET "
                "Pre_publication_description = %s, "
                "Post_publication_description = %s, "
                "Submitter = %s WHERE id = %s AND Owner = %s",
                ('Test Pre Pub', 'Test Post Pub', 'Rob', 1, 'Rob'))

    @pytest.mark.unit_test
    def test_fetch_phenotype(self):
        """Test that a single phenotype is fetched properly

        """
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            test_data = (
                35, "Test pre-publication", "Test post-publication",
                "Original description A", "cm^2", "pre-abbrev",
                "post-abbrev", "LAB001", "R. W.", "R. W.", "R. W."
            )
            cursor.fetchone.return_value = test_data
            phenotype = fetchone(db_mock,
                                 "Phenotype",
                                 where=Phenotype(id_=35, owner="Rob"))
            self.assertEqual(phenotype.id_, 35)
            self.assertEqual(phenotype.pre_pub_description,
                             "Test pre-publication")
            cursor.execute.assert_called_once_with(
                "SELECT * FROM Phenotype WHERE id = %s AND Owner = %s",
                (35, 'Rob'))

    @pytest.mark.unit_test
    def test_fetchall_metadataaudit(self):
        """Test that multiple metadata_audit entries are fetched properly

        """
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            test_data = (
                1, 35, "Rob", ('{"pages": '
                               '{"old": "5099-5109", '
                               '"new": "5099-5110"}, '
                               '"month": {"old": "July", '
                               '"new": "June"}, '
                               '"year": {"old": "2001", '
                               '"new": "2002"}}'),
                "2021-06-04 09:01:05")
            cursor.fetchall.return_value = (test_data,)
            metadata = list(fetchall(db_mock,
                                     "metadata_audit",
                                     where=MetadataAudit(dataset_id=35,
                                                         editor="Rob")))[0]
            self.assertEqual(metadata.dataset_id, 35)
            self.assertEqual(metadata.time_stamp,
                             "2021-06-04 09:01:05")
            cursor.execute.assert_called_once_with(
                ("SELECT * FROM metadata_audit WHERE "
                 "dataset_id = %s AND editor = %s"),
                (35, 'Rob'))

    @pytest.mark.unit_test
    # pylint: disable=R0201
    def test_probeset_called_with_right_columns(self):
        """Given a columns argument, test that the correct sql query is
        constructed"""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchall.return_value = None
            fetchone(db_mock,
                     "ProbeSet",
                     where=Probeset(name="1446112_at"),
                     columns=["OMIM", "Probe_set_target_region"])
            cursor.execute.assert_called_once_with(
                "SELECT OMIM, Probe_set_target_region FROM ProbeSet WHERE "
                "Name = %s",
                ("1446112_at",))

    @pytest.mark.unit_test
    def test_diff_from_dict(self):
        """Test that a correct diff is generated"""
        self.assertEqual(diff_from_dict({"id": 1, "data": "a"},
                                        {"id": 2, "data": "b"}),
                         {"id": {"old": 1, "new": 2},
                          "data": {"old": "a", "new": "b"}})
