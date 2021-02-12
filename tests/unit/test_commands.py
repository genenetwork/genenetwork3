"""Test cases for procedures defined in commands.py"""
import os
import unittest

from unittest import mock
from gn3.commands import compose_gemma_cmd


class TestCommands(unittest.TestCase):
    """Test cases for commands.py"""

    @mock.patch("gn3.commands.lookup_file")
    def test_compose_gemma_cmd_no_extra_args(self, mock_lookup_file):
        """Test that thhe gemma cmd is composed correctly"""
        metadata_file = os.path.join(os.path.dirname(__file__),
                                     "test_data/metadata.json")
        mock_lookup_file.side_effect = [metadata_file,
                                        "/tmp/genofile.txt",
                                        "/tmp/gf13Ad0tRX/phenofile.txt"]
        self.assertEqual(compose_gemma_cmd("gf13Ad0t",
                                           "metadata.json",
                                           gemma_wrapper_cmd="gemma-wrapper",
                                           gemma_wrapper_kwargs=None,
                                           gemma_kwargs=None,
                                           gemma_args=["-gk"]),
                         ("gemma-wrapper --json -- "
                          "-g /tmp/genofile.txt "
                          "-p /tmp/gf13Ad0tRX/phenofile.txt"
                          " -gk"))
