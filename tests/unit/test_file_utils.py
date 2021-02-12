"""Test cases for procedures defined in file_utils.py"""
import os
import unittest

from gn3.file_utils import get_dir_hash


class TestFileUtils(unittest.TestCase):
    """Test cases for procedures defined in file_utils.py"""
    def test_get_dir_hash(self):
        """Test that a directory is hashed correctly"""
        test_dir = os.path.join(os.path.dirname(__file__), "test_data")
        self.assertEqual("928a0e2e4846b4b3c2881d9c1d6cfce4",
                         get_dir_hash(test_dir))

    def test_get_dir_hash_non_existent_dir(self):
        """Test thata an error is raised when the dir does not exist"""
        self.assertRaises(FileNotFoundError,
                          get_dir_hash,
                          "/non-existent-file")
