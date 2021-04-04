"""module contains tests from datasets"""
import json

from unittest import TestCase
from unittest import mock

from collections import namedtuple

from gn3.computations.datasets import retrieve_trait_sample_data
from gn3.computations.datasets import get_query_for_dataset_sample
from gn3.computations.datasets import fetch_from_db_sample_data
from gn3.computations.datasets import create_dataset
from gn3.computations.datasets import dataset_creator_store
from gn3.computations.datasets import dataset_type_getter
from gn3.computations.datasets import fetch_dataset_type_from_gn2_api
from gn3.computations.datasets import fetch_dataset_sample_id
from gn3.computations.datasets import divide_into_chunks
from gn3.computations.datasets import get_traits_data


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

    @mock.patch("gn3.computations.datasets.dataset_creator_store")
    @mock.patch("gn3.computations.datasets.dataset_type_getter")
    def test_create_dataset(self, mock_dataset_type, mock_store):
        """test function that creates/fetches required dataset\
        can either be published phenotype,genotype,Microarray or\
        user defined ->Temp"""
        probe_name = "HC_M2_0606_P"
        probe_type = "ProbeSet"

        mock_dataset_creator = namedtuple(
            'ProbeSet', ["dataset_name", "dataset_type"])

        mock_store.return_value = mock_dataset_creator
        mock_dataset_type.return_value = probe_type
        dataset = create_dataset(
            dataset_type=None, dataset_name=probe_name)

        self.assertEqual(dataset.dataset_name, probe_name)
        self.assertEqual(dataset.dataset_type, probe_type)

    def test_dataset_creator_store(self):
        """test  for functions that actual
        function to create differerent \
        datasets"""
        results = dataset_creator_store("ProbeSet")

        self.assertTrue(results)

    def test_dataset_type_getter(self):
        """test for fetching type of dataset given\
        the dataset name"""

        redis_instance = mock.Mock()
        # found in redis
        redis_instance.get.return_value = "ProbeSet"
        results = dataset_type_getter("HC_M2_0_P", redis_instance)
        self.assertEqual(results, "ProbeSet")

    @mock.patch("gn3.computations.datasets.requests")
    def test_fetch_dataset_type_from_gn2_api(self, mock_request):
        """test for function that test fetching\
        all datasets from gn2 api in order to store\
        in redis"""

        expected_json_results = {"datasets": {
            "arabidopsis": {
                "BayXSha": {
                    "Genotypes": [
                        [
                            "None",
                            "BayXShaGeno",
                            "BayXSha Genotypes"
                        ]
                    ],
                    "Phenotypes": [
                        [
                            "642",
                            "BayXShaPublish",
                            "BayXSha Published Phenotypes"
                        ]
                    ]
                }
            }
        }}

        request_results = json.dumps(expected_json_results)
        mock_request.get.return_value.content = request_results
        results = fetch_dataset_type_from_gn2_api("HC_M2_0_P")
        expected_results = {
            "BayXShaGeno": "Geno",
            "642": "Publish"
        }

        self.assertEqual(expected_results, results)

    def test_fetch_dataset_sample_id(self):
        """get from the database the sample\
        id if only in the samplelists"""

        expected_results = {"B6D2F1": 1, "BXD1": 4, "BXD11": 10,
                            "BXD12": 11, "BXD13": 12, "BXD15": 14, "BXD16": 15}

        database_instance = mock.Mock()
        database_cursor = mock.Mock()

        database_cursor.execute.return_value = 5
        database_cursor.fetchall.return_value = list(expected_results.items())
        database_instance.cursor.return_value = database_cursor
        strain_list = ["B6D2F1", "BXD1", "BXD11",
                       "BXD12", "BXD13", "BXD16", "BXD15"]

        results = fetch_dataset_sample_id(
            samplelist=strain_list, database=database_instance, species="mouse")

        self.assertEqual(results, expected_results)

    @mock.patch("gn3.computations.datasets.fetch_from_db_sample_data")
    @mock.patch("gn3.computations.datasets.divide_into_chunks")
    def test_get_traits_data(self, mock_divide_into_chunks, mock_fetch_samples):
        """test for for function to get data\
        of traits in dataset"""
        # xtodo more tests needed for this

        _expected_results = {'AT_DSAFDS': [
            12, 14, 13, 23, 12, 14, 13, 23, 12, 14, 13, 23]}
        database = mock.Mock()
        sample_id = [1, 2, 7, 3, 22, 8]
        mock_divide_into_chunks.return_value = [
            [1, 2, 7], [3, 22, 8], [5, 22, 333]]
        mock_fetch_samples.return_value = ("AT_DSAFDS", 12, 14, 13, 23)
        results = get_traits_data(sample_id, database, "HC_M2", "Publish")

        self.assertEqual({}, dict(results))

    def test_divide_into_chunks(self):
        """test for dividing a list into given number of\
        chunks for example"""
        results = divide_into_chunks([1, 2, 7, 3, 22, 8, 5, 22, 333], 3)

        expected_results = [[1, 2, 7], [3, 22, 8], [5, 22, 333]]

        self.assertEqual(results, expected_results)
