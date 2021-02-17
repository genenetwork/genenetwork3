"""Integration tests for gemma API endpoints"""
import unittest

from unittest import mock
from gn3.app import create_app


class GemmaAPITest(unittest.TestCase):
    """Test cases for the Gemma API"""
    def setUp(self):
        self.app = create_app().test_client()

    @mock.patch("gn3.api.gemma.run_cmd")
    def test_get_version(self, mock_run_cmd):
        """Test that the correct response is returned"""
        mock_run_cmd.return_value = {"status": 0, "output": "v1.9"}
        response = self.app.get("/gemma/version", follow_redirects=True)
        self.assertEqual(response.get_json(),
                         {"status": 0, "output": "v1.9"})
        self.assertEqual(response.status_code, 200)
