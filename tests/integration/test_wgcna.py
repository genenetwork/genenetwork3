"""integration tests for wgcna"""

from unittest import TestCase
from unittest import mock

from gn3.app import create_app


class WgcnaIntegrationTest(TestCase):
    """class contains wgcna integration tests"""

    def setUp(self):
        self.app = create_app().test_client()

    @mock.patch("gn3.api.wgcna.call_wgcna_script")
    def test_wgcna_endpoint(self, mock_wgcna_api):
        """test /api/wgcna/run_wgcna endpoint"""

        wgcna_api_data = {
            "eigengenes": ["1224_at", "121412_at", "32342342-at"],
            "dendrogram_file_location": "/tmp/dend1.png"

        }
        mock_wgcna_api.return_value = wgcna_api_data

        request_data = {

            "trait_sample_data": [],


        }

        response = self.app.post("/api/wgcna/run_wgcna",
                                 json=request_data, follow_redirects=True)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json(), wgcna_api_data)
