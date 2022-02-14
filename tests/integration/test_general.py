"""Integration tests for some 'general' API endpoints"""
import os
import unittest
from unittest import mock

import pytest

from gn3.app import create_app


class GeneralAPITest(unittest.TestCase):
    """Test cases for 'general' API endpoints"""
    def setUp(self):
        self.app = create_app().test_client()

    @pytest.mark.integration_test
    def test_metadata_endpoint_exists(self):
        """Test that /metadata/upload exists"""
        response = self.app.post("/api/metadata/upload/d41d86-e4ceEo")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(),
                         {"status": 128,
                          "error": "Please provide a file!"})

    @pytest.mark.integration_test
    @mock.patch("gn3.api.general.extract_uploaded_file")
    def test_metadata_file_upload(self, mock_extract_upload):
        """Test correct upload of file"""
        mock_extract_upload.return_value = {
            "status": 0,
            "token": "d41d86-e4ceEo",
        }
        gzip_file = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            "../unit/upload-data.tar.gz"))
        response = self.app.post("/api/metadata/upload/d41d86-e4ceEo",
                                 data={"file": (gzip_file,
                                                "upload-data.tar.gz")})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json(),
                         {"status": 0,
                          "token": "d41d86-e4ceEo"})

    @pytest.mark.integration_test
    def test_metadata_file_wrong_upload(self):
        """Test that incorrect upload return correct status code"""
        response = self.app.post("/api/metadata/upload/d41d86-e4ceEo",
                                 data={"file": (__file__,
                                                "my_file")})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json(),
                         {"status": 128,
                          "error": "gzip failed to unpack file"})

    @pytest.mark.integration_test
    @mock.patch("gn3.api.general.run_cmd")
    def test_run_r_qtl(self, mock_run_cmd):
        """Test correct upload of file"""
        mock_run_cmd.return_value = "Random results from STDOUT"
        response = self.app.post("/api/qtl/run/"
                                 "geno_file_test/"
                                 "pheno_file_test")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json(),
                         "Random results from STDOUT")
