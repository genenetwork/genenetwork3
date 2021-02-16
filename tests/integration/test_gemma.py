"""Integration tests for gemma API endpoints"""
import unittest

from gn3.app import create_app


class GemmaAPITest(unittest.TestCase):
    """Test cases for the Gemma API"""
    def setUp(self):
        self.app = create_app().test_client()

    def test_gemma_index(self):
        """Test that the correct response is returned"""
        response = self.app.get("/gemma", follow_redirects=True)
        self.assertEqual(response.get_json().get("result"), "hello world")
