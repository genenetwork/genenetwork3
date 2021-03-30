"""module contains tests from datasets"""
from unittest import TestCase
from unittest import mock

from gn3.computations.datasets import retrieve_trait_sample_data
from gn3.computations.datasets import get_query_for_dataset_sample
from gn3.computations.datasets import fetch_from_db_sample_data


class TestDatasets(TestCase):
    """class contains tests for datasets"""

    @mock.patch("gn3.computations.datasets.fetch_from_db_sample_data")
    def test_retrieve_trait_sample_data(self, mock_fetch_sample_results):
        """test  retrieving sample data\
         for trait from the dataset"""
        trait_name = "1419792_at"
        dataset_id = "HC_M2_0606_P&"
        dataset_type = "Publish"

        dataset = {
            "id": dataset_id,
            "type": dataset_type,
            "name": dataset_id
        }

        fetch_results = [('BXD32', 8.001, None, None, 'BXD32')]

        mock_fetch_sample_results.return_value = fetch_results

        results = retrieve_trait_sample_data(
            dataset, trait_name)
        self.assertEqual(mock_fetch_sample_results.call_count, 1)
        self.assertEqual(results, fetch_results)

    def test_query_for_dataset_sample(self):
        """test for getting query for sample data"""

        no_results = get_query_for_dataset_sample("does not exists")

        query_exists = get_query_for_dataset_sample("Publish")

        self.assertEqual(no_results, None)
        self.assertIsInstance(query_exists, str)

    def test_fetch_from_db_sample_data(self):
        """test for function that fetches sample\
        results from the database"""

        database_results = [('BXD31', 8.001, None, None, 'BXD31'),
                            ('BXD32', 7.884, None, None, 'BXD32'),
                            ('BXD42', 7.682, None, None, 'BXD42'),
                            ('BXD42', 7.682, None, None, 'BXD42'),
                            ('BXD40', 7.945, None, None, 'BXD40'),
                            ('BXD43', 7.873, None, None, 'BXD43')
                            ]

        database = mock.Mock()
        db_cursor = mock.Mock()
        db_cursor.execute.return_value = 6
        db_cursor.fetchall.return_value = database_results
        database.cursor.return_value = db_cursor

        mock_pheno_query = """
                    SELECT
                            Strain.Name, PublishData.value, PublishSE.error,NStrain.count, Strain.Name2
                    WHERE
                            PublishXRef.InbredSetId = PublishFreeze.InbredSetId AND
                            PublishData.Id = PublishXRef.DataId AND PublishXRef.Id = 1419792_at AND
                            PublishFreeze.Id = '12' AND PublishData.StrainId = Strain.Id
                    Order BY
                            Strain.Name
                    """
        fetch_results = fetch_from_db_sample_data(mock_pheno_query, database)

        self.assertEqual(fetch_results, database_results)
