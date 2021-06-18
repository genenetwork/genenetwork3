"""Test cases for procedures defined in computations.rqtl"""
import unittest

from unittest import mock
from gn3.computations.rqtl import generate_rqtl_cmd

class TestRqtl(unittest.TestCase):
    """Test cases for computations.rqtl module"""
    @mock.patch("gn3.computations.rqtl.generate_hash_of_string")
    @mock.patch("gn3.computations.rqtl.get_hash_of_files")
    def test_generate_rqtl_command(self, mock_get_hash_files, mock_generate_hash_string):
        """Test computing mapping results with R/qtl"""
        mock_get_hash_files.return_value = "my-hash1"
        mock_generate_hash_string.return_value = "my-hash2"

        self.assertEqual(
            generate_rqtl_cmd(rqtl_wrapper_cmd="rqtl-wrapper",
                              rqtl_wrapper_kwargs={
                                  "g": "genofile",
                                  "p": "phenofile",
                                  "model": "normal",
                                  "method": "hk",
                                  "nperm": 1000,
                                  "scale": "Mb",
                                  "control": "rs123456"
                              },
                              rqtl_wrapper_bool_kwargs=[
                                  "addcovar",
                                  "interval"
                              ]), {
                                  "output_file":
                                  "my-hash1my-hash2my-hash2-output.csv",
                                  "rqtl_cmd": (
                                      "Rscript rqtl-wrapper "
                                      "--g genofile --p phenofile "
                                      "--model normal --method hk "
                                      "--nperm 1000 --scale Mb "
                                      "--control rs123456 "
                                      "--addcovar --interval"
                                  )
                              })
