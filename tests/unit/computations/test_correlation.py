"""module contains the tests for correlation"""
from unittest import TestCase
from unittest import mock
from collections import namedtuple

from gn3.computations.correlations import normalize_values
from gn3.computations.correlations import do_bicor
from gn3.computations.correlations import compute_sample_r_correlation
from gn3.computations.correlations import compute_all_sample_correlation
from gn3.computations.correlations import filter_shared_sample_keys
from gn3.computations.correlations import tissue_lit_corr_for_probe_type
from gn3.computations.correlations import tissue_correlation_for_trait_list
from gn3.computations.correlations import lit_correlation_for_trait_list
from gn3.computations.correlations import fetch_lit_correlation_data
from gn3.computations.correlations import query_formatter
from gn3.computations.correlations import map_to_mouse_gene_id


class QueryableMixin:
    """base class for db call"""

    def execute(self, query_options):
        """base method for execute"""
        raise NotImplementedError()

    def fetchone(self):
        """base method for fetching one iten"""
        raise NotImplementedError()

    def fetchall(self):
        """base method for fetch all items"""
        raise NotImplementedError()


class IllegalOperationError(Exception):
    """custom error to raise illegal operation in db"""

    def __init__(self):
        super().__init__("Operation not permitted!")


class DataBase(QueryableMixin):
    """Class for creating db object"""

    def __init__(self):
        self.__query_options = None
        self.__results = None

    def execute(self, query_options):
        """method to execute an sql query"""
        self.__query_options = query_options
        self.results_generator()
        return self

    def fetchone(self):
        """method to fetch single item from the db query"""
        if self.__results is None:
            raise IllegalOperationError()

        return self.__results[0]

    def fetchall(self):
        """method for fetching all items from db query"""
        if self.__results is None:
            raise IllegalOperationError()
        return self.__results

    def results_generator(self, expected_results=None):
        """private method  for generating mock results"""

        if expected_results is None:
            self.__results = [namedtuple("lit_coeff", "val")(x*0.1)
                              for x in range(1, 4)]
        else:
            self.__results = expected_results


class TestCorrelation(TestCase):
    """class for testing correlation functions"""

    def test_normalize_values(self):
        """function to test normalizing values """
        results = normalize_values([2.3, None, None, 3.2, 4.1, 5],
                                   [3.4, 7.2, 1.3, None, 6.2, 4.1])

        expected_results = ([2.3, 4.1, 5], [3.4, 6.2, 4.1], 3)

        self.assertEqual(results, expected_results)

    def test_bicor(self):
        """test for doing biweight mid correlation """

        results = do_bicor(x_val=[1, 2, 3], y_val=[4, 5, 6])

        self.assertEqual(results, ([1, 2, 3], [4, 5, 6])
                         )

    @mock.patch("gn3.computations.correlations.compute_corr_coeff_p_value")
    @mock.patch("gn3.computations.correlations.normalize_values")
    def test_compute_sample_r_correlation(self, norm_vals, compute_corr):
        """test for doing sample correlation gets the cor\
        and p value and rho value using pearson correlation"""
        primary_values = [2.3, 4.1, 5]
        target_values = [3.4, 6.2, 4.1]

        norm_vals.return_value = ([2.3, 4.1, 5, 4.2, 4, 1.2],
                                  [3.4, 6.2, 4, 1.1, 8, 1.1], 6)
        compute_corr.side_effect = [(0.7, 0.3), (-1.0, 0.9), (1, 0.21)]

        pearson_results = compute_sample_r_correlation(corr_method="pearson",
                                                       trait_vals=primary_values,
                                                       target_samples_vals=target_values)

        spearman_results = compute_sample_r_correlation(corr_method="spearman",
                                                        trait_vals=primary_values,
                                                        target_samples_vals=target_values)

        bicor_results = compute_sample_r_correlation(corr_method="bicor",
                                                     trait_vals=primary_values,
                                                     target_samples_vals=target_values)

        self.assertEqual(bicor_results, (1, 0.21, 6))
        self.assertEqual(pearson_results, (0.7, 0.3, 6))
        self.assertEqual(spearman_results, (-1.0, 0.9, 6))

        self.assertIsInstance(
            pearson_results, tuple, "message")
        self.assertIsInstance(
            spearman_results, tuple, "message")

    def test_filter_shared_sample_keys(self):
        """function to  tests shared key between two dicts"""

        this_samplelist = {
            "C57BL/6J": "6.638",
            "DBA/2J": "6.266",
            "B6D2F1": "6.494",
            "D2B6F1": "6.565",
            "BXD2": "6.456"
        }

        target_samplelist = {
            "DBA/2J": "1.23",
            "D2B6F1": "6.565",
            "BXD2": "6.456"

        }

        filtered_target_samplelist = ["1.23", "6.565", "6.456"]
        filtered_this_samplelist = ["6.266", "6.565", "6.456"]

        results = filter_shared_sample_keys(
            this_samplelist=this_samplelist, target_samplelist=target_samplelist)

        self.assertEqual(results, (filtered_this_samplelist,
                                   filtered_target_samplelist))

    @mock.patch("gn3.computations.correlations.compute_sample_r_correlation")
    @mock.patch("gn3.computations.correlations.filter_shared_sample_keys")
    def test_compute_all_sample(self, filter_shared_samples, sample_r_corr):
        """given target dataset compute all sample r correlation"""

        filter_shared_samples.return_value = (["1.23", "6.565", "6.456"], [
            "6.266", "6.565", "6.456"])
        sample_r_corr.return_value = ([-1.0, 0.9, 6])

        this_trait_data = {
            "C57BL/6J": "6.638",
            "DBA/2J": "6.266",
            "B6D2F1": "6.494",
            "D2B6F1": "6.565",
            "BXD2": "6.456"
        }

        traits_dataset = [{
            "DBA/2J": "1.23",
            "D2B6F1": "6.565",
            "BXD2": "6.456"
        }]

        sample_all_results = [{"corr_coeffient": -1.0,
                               "p_value": 0.9,
                               "num_overlap": 6}]
        # ?corr_method: str, trait_vals, target_samples_vals

        self.assertEqual(compute_all_sample_correlation(
            this_trait=this_trait_data, target_dataset=traits_dataset), sample_all_results)
        sample_r_corr.assert_called_once_with(
            corr_method="pearson", trait_vals=['1.23', '6.565', '6.456'],
            target_samples_vals=['6.266', '6.565', '6.456'])
        filter_shared_samples.assert_called_once_with(
            this_trait_data, traits_dataset[0])

    def test_tissue_lit_corr_for_probe_type(self):
        """tests for doing tissue and lit correlation for  trait list\
        if both the dataset and target dataset are probeset"""

        results = tissue_lit_corr_for_probe_type(this_dataset_type=None,
                                                 target_dataset_type=None)

        self.assertEqual(results, (None, None))

    @mock.patch("gn3.computations.correlations.compute_corr_coeff_p_value")
    def test_tissue_correlation_for_trait_list(self, mock_compute_corr_coeff):
        """test given a primary tissue values for a trait  and and a list of\
        target tissues for traits  do the tissue correlation for them"""

        primary_tissue_values = [1.1, 1.5, 2.3]
        target_tissues_values = [[1, 2, 3], [3, 4, 1]]
        mock_compute_corr_coeff.side_effect = [(0.4, 0.9), (-0.2, 0.91)]
        expected_tissue_results = [{'tissue_corr': 0.4, 'p_value': 0.9, "tissue_number": 3},
                                   {'tissue_corr': -0.2, 'p_value': 0.91, "tissue_number": 3}]

        tissue_results = tissue_correlation_for_trait_list(
            primary_tissue_values, target_tissues_values,
            corr_method="pearson", compute_corr_p_value=mock_compute_corr_coeff)

        self.assertEqual(tissue_results, expected_tissue_results)

    @mock.patch("gn3.computations.correlations.fetch_lit_correlation_data")
    @mock.patch("gn3.computations.correlations.map_to_mouse_gene_id")
    def test_lit_correlation_for_trait_list(self, mock_mouse_gene_id, fetch_lit_data):
        """fetch results from  db call for lit correlation given a trait list\
        after doing correlation"""

        target_trait_lists = [{"gene_id": 15},
                              {"gene_id": 17},
                              {"gene_id": 11}]
        mock_mouse_gene_id.side_effect = [12, 11, 18, 16, 20]

        database_instance = namedtuple("database", "execute")("fetchone")

        fetch_lit_data.side_effect = [(15, 9), (17, 8), (11, 12)]

        lit_results = lit_correlation_for_trait_list(
            database=database_instance, target_trait_lists=target_trait_lists,
            species="rat", trait_gene_id="12")

        expected_results = [{"gene_id": 15, "lit_corr": 9}, {
            "gene_id": 17, "lit_corr": 8}, {"gene_id": 11, "lit_corr": 12}]

        self.assertEqual(lit_results, expected_results)

    def test_fetch_lit_correlation_data(self):
        """test for fetching lit correlation data from\
        the database where the input and mouse geneid are none"""

        database_instance = DataBase()
        results = fetch_lit_correlation_data(database=database_instance,
                                             gene_id="1",
                                             input_mouse_gene_id=None,
                                             mouse_gene_id=None)

        self.assertEqual(results, ("1", 0))

    def test_fetch_lit_correlation_data_db_query(self):
        """test for fetching lit corr coefficent givent the input\
         input trait mouse gene id and mouse gene id"""

        database_instance = DataBase()
        expected_results = ("1", 0.1)

        lit_results = fetch_lit_correlation_data(database=database_instance,
                                                 gene_id="1",
                                                 input_mouse_gene_id="20",
                                                 mouse_gene_id="15")

        self.assertEqual(expected_results, lit_results)

    def test_query_lit_correlation_for_db_empty(self):
        """test that corr coeffient returned is 0 given the\
        db value if corr coefficient is empty"""
        database_instance = mock.Mock()
        database_instance.execute.return_value.fetchone.return_value = None

        lit_results = fetch_lit_correlation_data(database=database_instance,
                                                 input_mouse_gene_id="12",
                                                 gene_id="16",
                                                 mouse_gene_id="12")

        self.assertEqual(lit_results, ("16", 0))

    def test_query_formatter(self):
        """test for formatting a query given the query string and also the\
        values"""
        query = """
        SELECT VALUE
        FROM  LCorr
        WHERE GeneId1='%s' and
        GeneId2='%s'
        """

        expected_formatted_query = """
        SELECT VALUE
        FROM  LCorr
        WHERE GeneId1='20' and
        GeneId2='15'
        """

        mouse_gene_id = "20"
        input_mouse_gene_id = "15"

        query_values = (mouse_gene_id, input_mouse_gene_id)

        formatted_query = query_formatter(query, *query_values)

        self.assertEqual(formatted_query, expected_formatted_query)

    def test_query_formatter_no_query_values(self):
        """test for formatting a query where there are no\
        string placeholder"""
        query = """SELECT * FROM  USERS"""
        formatted_query = query_formatter(query)

        self.assertEqual(formatted_query, query)

    def test_map_to_mouse_gene_id(self):
        """test for converting a gene id to mouse geneid\
        given a species which is not mouse"""
        database_instance = mock.Mock()
        test_data = [("Human", 14), (None, 9), ("Mouse", 15), ("Rat", 14)]

        database_results = [namedtuple("mouse_id", "mouse")(val)
                            for val in range(12, 20)]
        results = []

        database_instance.execute.return_value.fetchone.side_effect = database_results
        expected_results = [12, None, 13, 14]
        for (species, gene_id) in test_data:

            mouse_gene_id_results = map_to_mouse_gene_id(
                database=database_instance, species=species, gene_id=gene_id)
            results.append(mouse_gene_id_results)

        self.assertEqual(results, expected_results)
