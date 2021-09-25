"""module contains python code for wgcna"""
from unittest import skip
from unittest import TestCase
from unittest import mock

from gn3.computations.wgcna import dump_wgcna_data
from gn3.computations.wgcna import compose_wgcna_cmd
from gn3.computations.wgcna import call_wgcna_script


class TestWgcna(TestCase):
    """test class for wgcna"""

    @mock.patch("gn3.computations.wgcna.dump_wgcna_data")
    def test_call_wgcna_script(self, mock_dump):
        """call wgcna script"""

        mock_dump.return_value = "/tmp/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc-test.json"

        results = call_wgcna_script(
            "/home/kabui/project/genenetwork3/scripts/wgcna_analysis.R", {})

        self.assertEqual(results, "dsedf")

    def test_compose_wgcna_cmd(self):
        """test for composing wgcna cmd"""
        wgcna_cmd = compose_wgcna_cmd(
            "wgcna.r", "/tmp/wgcna.json")
        self.assertEqual(
            wgcna_cmd, "Rscript ./scripts/wgcna.r  /tmp/wgcna.json")

    @skip("to  update tests")
    def test_create_json_file(self):
        """test for writing the data to a csv file"""
        # # All the traits we have data for (should not contain duplicates)
        # All the strains we have data for (contains duplicates)

        trait_sample_data = {"1425642_at": {"129S1/SvImJ": 7.142,
                                            "A/J": 7.31, "AKR/J": 7.49,
                                            "B6D2F1": 6.899, "BALB/cByJ": 7.172,
                                            "BALB/cJ": 7.396},
                             "1457784_at": {"129S1/SvImJ": 7.071, "A/J": 7.05,
                                            "AKR/J": 7.313,
                                            "B6D2F1": 6.999, "BALB/cByJ": 7.293,
                                            "BALB/cJ": 7.117},
                             "1444351_at": {"129S1/SvImJ": 7.221, "A/J": 7.246,
                                            "AKR/J": 7.754,
                                            "B6D2F1": 6.866, "BALB/cByJ": 6.752,
                                            "BALB/cJ": 7.269}

                             }

        expected_input = {
            "trait_sample_data": trait_sample_data,
            "TOMtype": "unsigned",
            "minModuleSize": 30
        }

        results = dump_wgcna_data(
            expected_input)

        self.assertEqual(results, {})
