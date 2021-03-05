"""Test cases for procedures defined in computations.gemma"""
import unittest

from unittest import mock
from gn3.computations.gemma import compute_k_values
from gn3.computations.gemma import generate_hash_of_string
from gn3.computations.gemma import generate_pheno_txt_file
from gn3.computations.gemma import generate_gemma_computation_cmd


class TestGemma(unittest.TestCase):
    """Test cases for computations.gemma module"""
    def test_generate_pheno_txt_file(self):
        """Test that the pheno text file is generated correctly"""
        open_mock = mock.mock_open()
        with mock.patch("gn3.computations.gemma.open", open_mock, create=True):
            _file = generate_pheno_txt_file(tmpdir="/tmp",
                                            trait_filename="phenotype.txt",
                                            values=["x", "x", "BXD07 438.700"])
            self.assertEqual(_file, ("/tmp/gn2/phenotype_"
                                     "P7y6QWnwBPedSZdL0+m/GQ.txt"))
        open_mock.assert_called_with(("/tmp/gn2/phenotype_"
                                      "P7y6QWnwBPedSZdL0+m/GQ.txt"), "w")
        open_mock.return_value.write.assert_has_calls([
            mock.call("NA\n"),
            mock.call("NA\n"),
            mock.call("BXD07 438.700\n")
        ])

    def test_generate_hash_of_string(self):
        """Test that a string is hashed correctly"""
        self.assertEqual(generate_hash_of_string("I^iQP&TlSR^z"),
                         "hMVRw8kbEp49rOmoIkhMjA")

    @mock.patch("gn3.computations.gemma.do_paths_exist")
    def test_compose_k_computation_cmd(self, mock_pathsp):
        """Test that a K computation cmd is constructed properly"""
        mock_pathsp.return_value = True
        self.assertEqual(
            generate_gemma_computation_cmd(
                gemma_cmd="gemma-wrapper",
                gemma_wrapper_kwargs=None,
                gemma_kwargs={
                    "geno_filename": "genofile.txt",
                    "trait_filename": "test.txt",
                    "covar_filename": "genofile_snps.txt"
                },
                output_file="/tmp/gn2/k_output_gUFhGu4rLG7k+CXLPk1OUg.txt",
            ), ("gemma-wrapper --json -- "
                "-g genofile.txt -p "
                "test.txt -a genofile_snps.txt "
                "-gk > /tmp/gn2/"
                "k_output_gUFhGu4rLG7k+CXLPk1OUg.txt"))

    @mock.patch("gn3.computations.gemma.get_hash_of_files")
    def test_compute_k_values_without_loco(self, mock_get_hash):
        """Test computing k valuse without loco"""
        mock_get_hash.return_value = "my-hash"
        self.assertEqual(
            compute_k_values(gemma_cmd="gemma-wrapper",
                             output_dir="/tmp",
                             token="my-token",
                             gemma_kwargs={
                                 "g": "genofile",
                                 "p": "phenofile",
                                 "a": "snpsfile"
                             }), {
                                 "output_file":
                                 "my-hash-k-output.json",
                                 "gemma_cmd":
                                 ("gemma-wrapper --json -- -g genofile "
                                  "-p phenofile -a snpsfile "
                                  "-gk > /tmp/my-token/my-hash-k-output.json")
                             })

    @mock.patch("gn3.computations.gemma.get_hash_of_files")
    def test_compute_k_values_with_loco(self, mock_get_hash):
        """Test computing k valuse with loco"""
        mock_get_hash.return_value = "my-hash"
        self.assertEqual(
            compute_k_values(gemma_cmd="gemma-wrapper",
                             output_dir="/tmp",
                             token="my-token",
                             chromosomes="1,2,3,4,5",
                             gemma_kwargs={
                                 "g": "genofile",
                                 "p": "phenofile",
                                 "a": "snpsfile"
                             }), {
                                 "output_file":
                                 "my-hash-r+gF5a-k-output.json",
                                 "gemma_cmd": ("gemma-wrapper --json "
                                               "--loco --input 1,2,3,4,5 "
                                               "-- -g genofile "
                                               "-p phenofile -a snpsfile "
                                               "-gk > /tmp/my-token/"
                                               "my-hash-r+gF5a-k-output.json")
                             })
