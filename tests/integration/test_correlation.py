"""Integration tests for correlation api"""
import unittest

from gn3.app import create_app


class CorrelationAPITest(unittest.TestCase):
    """Test cases for the Gemma API"""
    def setUp(self):
        self.app = create_app().test_client()

    def test_corr_compute(self):
        """Test that the correct response in correlation"""
        post_data = """
        """
        response = self.app.post("/corr_compute", data=post_data,follow_redirects=True)
        # self.assertEqual(response.get_json().get("result"), "hello world")
        self.assertEqual(response.status_code,500)
