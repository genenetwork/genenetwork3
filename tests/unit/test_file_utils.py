"""Test cases for procedures defined in file_utils.py"""
import os
import unittest

from dataclasses import dataclass
from typing import Callable
from unittest import mock
from gn3.file_utils import extract_uploaded_file
from gn3.file_utils import get_dir_hash
from gn3.file_utils import jsonfile_to_dict


@dataclass
class MockFile:
    """Mock File object returned by request.files"""
    filename: str
    save: Callable


class TestFileUtils(unittest.TestCase):
    """Test cases for procedures defined in file_utils.py"""
    def test_get_dir_hash(self):
        """Test that a directory is hashed correctly"""
        test_dir = os.path.join(os.path.dirname(__file__), "test_data")
        self.assertEqual("fd9d74a9554b7f13bfeffbdda8e61486",
                         get_dir_hash(test_dir))

    def test_get_dir_hash_non_existent_dir(self):
        """Test thata an error is raised when the dir does not exist"""
        self.assertRaises(FileNotFoundError,
                          get_dir_hash,
                          "/non-existent-file")

    def test_jsonfile_to_dict(self):
        """Test that a json file is parsed correctly"""""
        json_file = os.path.join(os.path.dirname(__file__),
                                 "test_data", "metadata.json")
        self.assertEqual("Longer description",
                         jsonfile_to_dict(json_file).get("description"))

    def test_jsonfile_to_dict_nonexistent_file(self):
        """Test that a ValueError is raised when the json file is
non-existent"""
        self.assertRaises(FileNotFoundError,
                          jsonfile_to_dict,
                          "/non-existent-dir")

    @mock.patch("gn3.file_utils.tarfile")
    @mock.patch("gn3.file_utils.secure_filename")
    def test_extract_uploaded_file(self, mock_file, mock_tarfile):
        """Test that the gzip file is extracted to the right location"""
        mock_file.return_value = "upload-data.tar.gz"
        mock_fileobj = MockFile(save=mock.MagicMock(),
                                filename="upload-data.tar.gz")
        mock_tarfile.return_value = mock.Mock()
        result = extract_uploaded_file(mock_fileobj, "/tmp",
                                       token="abcdef-abcdef")
        mock_fileobj.save.assert_called_once_with("/tmp/abcdef-abcdef/"
                                                  "upload-data.tar.gz")
        mock_file.assert_called_once_with("upload-data.tar.gz")
        self.assertEqual(result,
                         {"status": 0,
                          "token": "abcdef-abcdef"})

    @mock.patch("gn3.file_utils.secure_filename")
    def test_extract_uploaded_file_non_existent_gzip(self, mock_file):
        """Test that the right error message is returned when there is a problem
extracting the file"""
        mock_file.return_value = os.path.join(
            os.path.dirname(__file__),
            "CTtyodSTh5")  # Does not exist!
        mock_fileobj = MockFile(save=mock.MagicMock(),
                                filename="")
        result = extract_uploaded_file(mock_fileobj, "/tmp")
        self.assertEqual(result,
                         {"status": 128,
                          "error": "gzip failed to unpack file"})
