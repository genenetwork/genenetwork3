"""Test cases for procedures defined in fs_helpers.py"""
import os
import unittest

from dataclasses import dataclass
from typing import Callable
from unittest import mock
import pytest
from gn3.fs_helpers import extract_uploaded_file
from gn3.fs_helpers import get_dir_hash
from gn3.fs_helpers import jsonfile_to_dict
from gn3.fs_helpers import cache_ipfs_file


@dataclass
class MockFile:
    """Mock File object returned by request.files"""
    filename: str
    save: Callable


class TestFileUtils(unittest.TestCase):
    """Test cases for procedures defined in fs_helpers.py"""

    @pytest.mark.unit_test
    def test_get_dir_hash(self):
        """Test that a directory is hashed correctly"""
        test_dir = os.path.join(os.path.dirname(__file__), "test_data")
        self.assertEqual("3aeafab7d53b4f76d223366ae7ee9738",
                         get_dir_hash(test_dir))

    @pytest.mark.unit_test
    def test_get_dir_hash_non_existent_dir(self):
        """Test thata an error is raised when the dir does not exist"""
        self.assertRaises(FileNotFoundError, get_dir_hash,
                          "/non-existent-file")

    @pytest.mark.unit_test
    def test_jsonfile_to_dict(self):
        """Test that a json file is parsed correctly""" ""
        json_file = os.path.join(os.path.dirname(__file__), "test_data",
                                 "metadata.json")
        self.assertEqual("Longer description",
                         jsonfile_to_dict(json_file).get("description"))

    @pytest.mark.unit_test
    def test_jsonfile_to_dict_nonexistent_file(self):
        """Test that a ValueError is raised when the json file is
non-existent"""
        self.assertRaises(FileNotFoundError, jsonfile_to_dict,
                          "/non-existent-dir")

    @pytest.mark.unit_test
    @mock.patch("gn3.fs_helpers.tarfile")
    @mock.patch("gn3.fs_helpers.secure_filename")
    def test_extract_uploaded_file(self, mock_file, mock_tarfile):
        """Test that the gzip file is extracted to the right location"""
        mock_file.return_value = "upload-data.tar.gz"
        mock_fileobj = MockFile(save=mock.MagicMock(),
                                filename="upload-data.tar.gz")
        mock_tarfile.return_value = mock.Mock()
        result = extract_uploaded_file(mock_fileobj,
                                       "/tmp",
                                       token="abcdef-abcdef")
        mock_fileobj.save.assert_called_once_with("/tmp/abcdef-abcdef/"
                                                  "upload-data.tar.gz")
        mock_tarfile.open.assert_called_once_with("/tmp/abcdef-abcdef/"
                                                  "upload-data.tar.gz")
        mock_tarfile.open.return_value.__enter__.return_value.extractall.assert_called_once_with(
            path='/tmp/abcdef-abcdef')
        mock_file.assert_called_once_with("upload-data.tar.gz")
        self.assertEqual(result, {"status": 0, "token": "abcdef-abcdef"})

    @pytest.mark.unit_test
    @mock.patch("gn3.fs_helpers.secure_filename")
    def test_extract_uploaded_file_non_existent_gzip(self, mock_file):
        """Test that the right error message is returned when there is a problem
extracting the file"""
        mock_file.return_value = os.path.join(os.path.dirname(__file__),
                                              "CTtyodSTh5")  # Does not exist!
        mock_fileobj = MockFile(save=mock.MagicMock(), filename="")
        result = extract_uploaded_file(mock_fileobj, "/tmp")
        self.assertEqual(result, {
            "status": 128,
            "error": "gzip failed to unpack file"
        })

    @pytest.mark.unit_test
    def test_cache_ipfs_file_cache_hit(self):
        """Test that the correct file location is returned if there's a cache hit"""
        # Create empty file
        test_dir = "/tmp/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc-test"
        if not os.path.exists(test_dir):
            os.mkdir(test_dir)
        with open(f"{test_dir}/genotype.txt", "a", encoding="utf8"):
            pass
        file_loc = cache_ipfs_file(
            ipfs_file=("/ipfs/"
                       "QmQPeNsJPyVWPFDVHb"
                       "77w8G42Fvo15z4bG2X8D2GhfbSXc-test/"
                       "genotype.txt"),
            cache_dir="/tmp")
        # Clean up
        os.remove(f"{test_dir}/genotype.txt")
        os.rmdir(test_dir)
        self.assertEqual(file_loc, f"{test_dir}/genotype.txt")

    @pytest.mark.unit_test
    @mock.patch("gn3.fs_helpers.ipfshttpclient")
    def test_cache_ipfs_file_cache_miss(self,
                                        mock_ipfs):
        """Test that a file is cached if there's a cache miss"""
        mock_ipfs_client = mock.MagicMock()
        mock_ipfs.connect.return_value = mock_ipfs_client

        test_dir = "/tmp/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc-test"
        self.assertEqual(cache_ipfs_file(
            ipfs_file=("/ipfs/"
                       "QmQPeNsJPyVWPFDVHb"
                       "77w8G42Fvo15z4bG2X8D2GhfbSXc-test/"
                       "genotype.txt"),
            cache_dir="/tmp"
        ), f"{test_dir}/genotype.txt")
        mock_ipfs_client.get.assert_called_once_with(
            ("/ipfs/"
             "QmQPeNsJPyVWPFDVHb"
             "77w8G42Fvo15z4bG2X8D2GhfbSXc-test/"
             "genotype.txt"),
            target=f"{test_dir}"
        )
