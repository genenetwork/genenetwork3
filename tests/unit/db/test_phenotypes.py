"""Tests for db/phenotypes.py"""
from unittest import TestCase
from unittest import mock

from gn3.db import fetchone
from gn3.db import update
from gn3.db import diff_from_dict
from gn3.db.phenotypes import Phenotype


class TestPhenotypes(TestCase):
    """Test cases for fetching chromosomes"""
    def test_update_phenotype_with_no_data(self):
        """Test that a phenotype is updated correctly if an empty Phenotype dataclass
        is provided

        """
        db_mock = mock.MagicMock()
        self.assertEqual(update(
            conn=db_mock, table="Phenotype",
            data=Phenotype(), where=Phenotype()), None)

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
                where=Phenotype(id_=1)), 1)
            cursor.execute.assert_called_once_with(
                "UPDATE Phenotype SET "
                "Pre_publication_description = "
                "'Test Pre Pub', "
                "Post_publication_description = "
                "'Test Post Pub', Submitter = 'Rob' "
                "WHERE id = '1'"
            )

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
                                 where=Phenotype(id_=35))
            self.assertEqual(phenotype.id_, 35)
            self.assertEqual(phenotype.pre_pub_description,
                             "Test pre-publication")
            cursor.execute.assert_called_once_with(
                "SELECT * FROM Phenotype WHERE id = '35'")

    def test_diff_from_dict(self):
        """Test that a correct diff is generated"""
        self.assertEqual(diff_from_dict({"id": 1, "data": "a"},
                                        {"id": 2, "data": "b"}),
                         {"id": {"old": 1, "new": 2},
                          "data": {"old": "a", "new": "b"}})
