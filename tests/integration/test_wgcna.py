"""integration tests for wgcna"""

from unittest import TestCase
from unittest import mock

import pytest

from gn3.app import create_app


class WgcnaIntegrationTest(TestCase):
    """class contains wgcna integration tests"""

    def setUp(self):
        self.app = create_app().test_client()

    @pytest.mark.integration_test
    @mock.patch("gn3.api.wgcna.call_wgcna_script")
    def test_wgcna_endpoint(self, mock_wgcna_script):
        """test /api/wgcna/run_wgcna endpoint"""

        wgcna_output_data = {
            "code": 0,
            "output": "run script successfully",
            "data": {
                "ModEigens": {
                    "MEturquoise": [
                        0.0646677768085351,
                        0.137200224277058,
                        0.63451113720732,
                        -0.544002665501479,
                        -0.489487590361863,
                        0.197111117570427
                    ]
                },
                "net_colors": {
                    "X1": "turquoise",
                    "X2": "turquoise",
                    "X3": "turquoise",
                    "X4": "turquoise"
                },
                "imageLoc": "/WGCNAoutput_1uujpTIpC.png"
            }
        }

        request_data = {
            "trait_names": [
                "1455537_at",
                "1425637_at"
            ],
            "trait_sample_data": [
                {
                    "129S1/SvImJ": 6.142,
                    "A/J": 5.31,
                    "AKR/J": 3.49,
                    "B6D2F1": 2.899,
                    "BALB/cByJ": 1.172,
                    "BALB/cJ": 7.396
                },
                {
                    "129S1/SvImJ": 1.42,
                    "A/J": 2.31,
                    "AKR/J": 5.49,
                    "B6D2F1": 3.899,
                    "BALB/cByJ": 1.172,
                    "BALB/cJ": 7.396
                }
            ]
        }
        mock_wgcna_script.return_value = wgcna_output_data

        response = self.app.post("/api/wgcna/run_wgcna",
                                 json=request_data, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), wgcna_output_data)
