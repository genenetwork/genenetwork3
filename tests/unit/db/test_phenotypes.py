"""Tests for db/phenotypes.py"""
from unittest import TestCase
from unittest import mock

from gn3.db.phenotypes import Phenotype
from gn3.db.phenotypes import update_phenotype


class TestPhenotypes(TestCase):
    """Test cases for fetching chromosomes"""
    def test_update_phenotype_with_no_data(self):
        """
        Test that a phenotype is updated correctly if an empty Phenotype dataclass
        is provided
        """
        db_mock = mock.MagicMock()
        self.assertEqual(update_phenotype(
            db_mock, data=Phenotype(), where=Phenotype()), None)

    def test_update_phenotype_with_data(self):
        """
        Test that a phenotype is updated correctly if some
        data is provided
        """
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            type(cursor).rowcount = 1
            self.assertEqual(update_phenotype(
                db_mock, data=Phenotype(
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
