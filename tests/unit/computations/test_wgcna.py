"""module contains python code for wgcna"""
from unittest import TestCase
from unittest import mock

from gn3.computations.wgcna import dump_wgcna_data
from gn3.computations.wgcna import compose_wgcna_cmd
from gn3.computations.wgcna import call_wgcna_script


class TestWgcna(TestCase):
    """test class for wgcna"""

    @mock.patch("gn3.computations.wgcna.process_image")
    @mock.patch("gn3.computations.wgcna.run_cmd")
    @mock.patch("gn3.computations.wgcna.compose_wgcna_cmd")
    @mock.patch("gn3.computations.wgcna.dump_wgcna_data")
    def test_call_wgcna_script(self,
                               mock_dumping_data,
                               mock_compose_wgcna,
                               mock_run_cmd,
                               mock_img,
                               ):
        """test for calling wgcna script"""

        # pylint: disable = line-too-long
        mock_dumping_data.return_value = "/tmp/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc-test.json"

        mock_compose_wgcna.return_value = "Rscript/GUIX_PATH/scripts/r_file.R /tmp/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc-test.json"

        request_data = {
            "trait_names": ["1455537_at", "1425637_at", "1449593_at", "1421945_a_at", "1450423_s_at", "1423841_at", "1451144_at"],
            "trait_sample_data": [
                {
                    "129S1/SvImJ": 7.142,
                    "A/J": 7.31,
                    "AKR/J": 7.49,
                    "B6D2F1": 6.899,
                    "BALB/cByJ": 7.172,
                    "BALB/cJ": 7.396
                },
                {
                    "129S1/SvImJ": 7.071,
                    "A/J": 7.05,
                    "AKR/J": 7.313,
                    "B6D2F1": 6.999,
                    "BALB/cByJ": 7.293,
                    "BALB/cJ": 7.117
                }]}

        mock_run_cmd_results = {

            "code": 0,
            "output": "Flagging genes and samples with too many missing values...\n  ..step 1\nAllowing parallel execution with up to 3 working processes.\npickSoftThreshold: will use block size 7.\n pickSoftThreshold: calculating connectivity for given powers...\n   ..working on genes 1 through 7 of 7\n   Flagging genes and samples with too many missing values...\n    ..step 1\n ..Working on block 1 .\n    TOM calculation: adjacency..\n    ..will not use multithreading.\nclustering..\n ....detecting modules..\n ....calculating module eigengenes..\n ....checking kME in modules..\n ..merging modules that are too close..\n     mergeCloseModules: Merging modules whose distance is less than 0.15\n     mergeCloseModules: less than two proper modules.\n      ..color levels are turquoise\n      ..there is nothing to merge.\n       Calculating new MEs...\n"
        }

        json_output = "{\"inputdata\":{\"trait_sample_data \":{},\"minModuleSize\":30,\"TOMtype\":\"unsigned\"},\"output\":{\"eigengenes\":[],\"imageLoc\":[],\"colors\":[]}}"

        expected_output = {

            "data": {
                "inputdata": {
                    "trait_sample_data ": {},
                    "minModuleSize": 30,
                    "TOMtype": "unsigned"
                },

                "output": {
                    "eigengenes": [],
                    "imageLoc": [],
                    "colors": [],
                    "image_data": "AFDSFNBSDGJJHH"
                }
            },

            **mock_run_cmd_results

        }

        with mock.patch("builtins.open", mock.mock_open(read_data=json_output)):

            mock_run_cmd.return_value = mock_run_cmd_results
            mock_img.return_value = b"AFDSFNBSDGJJHH"

            results = call_wgcna_script(
                "Rscript/GUIX_PATH/scripts/r_file.R", request_data)

            mock_dumping_data.assert_called_once_with(request_data)

            mock_compose_wgcna.assert_called_once_with(
                "Rscript/GUIX_PATH/scripts/r_file.R",
                "/tmp/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc-test.json")

            mock_run_cmd.assert_called_once_with(
                "Rscript/GUIX_PATH/scripts/r_file.R /tmp/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc-test.json")

            self.assertEqual(results, expected_output)

    @mock.patch("gn3.computations.wgcna.run_cmd")
    @mock.patch("gn3.computations.wgcna.compose_wgcna_cmd")
    @mock.patch("gn3.computations.wgcna.dump_wgcna_data")
    def test_call_wgcna_script_fails(self, mock_dumping_data, mock_compose_wgcna, mock_run_cmd):
        """test for calling wgcna script\
        fails and generates the expected error"""
        # pylint: disable = line-too-long,
        mock_dumping_data.return_value = "/tmp/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc-test.json"

        mock_compose_wgcna.return_value = "Rscript/GUIX_PATH/scripts/r_file.R /tmp/QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc-test.json"

        expected_error = {
            "code": 2,
            "output": "could not read the json file"
        }

        with mock.patch("builtins.open", mock.mock_open(read_data="")):

            mock_run_cmd.return_value = expected_error
            self.assertEqual(call_wgcna_script(
                "input_file.R", ""), expected_error)

    def test_compose_wgcna_cmd(self):
        """test for composing wgcna cmd"""
        wgcna_cmd = compose_wgcna_cmd(
            "wgcna.r", "/tmp/wgcna.json")
        self.assertEqual(
            wgcna_cmd, "Rscript ./scripts/wgcna.r  /tmp/wgcna.json")

    @mock.patch("gn3.computations.wgcna.TMPDIR", "/tmp")
    @mock.patch("gn3.computations.wgcna.uuid.uuid4")
    def test_create_json_file(self, file_name_generator):
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

        with mock.patch("builtins.open", mock.mock_open()) as file_handler:

            file_name_generator.return_value = "facb73ff-7eef-4053-b6ea-e91d3a22a00c"

            results = dump_wgcna_data(
                expected_input)

            file_handler.assert_called_once_with(
                "/tmp/facb73ff-7eef-4053-b6ea-e91d3a22a00c.json", 'w')

            self.assertEqual(
                results, "/tmp/facb73ff-7eef-4053-b6ea-e91d3a22a00c.json")
