"""Module contains the unittest for rqtl2 functions  """
# pylint: disable=C0301
from unittest import mock
import pytest
from gn3.computations.rqtl2 import compose_rqtl2_cmd
from gn3.computations.rqtl2 import generate_rqtl2_files
from gn3.computations.rqtl2 import prepare_files
from gn3.computations.rqtl2 import validate_required_keys


@pytest.mark.unit_test
@mock.patch("gn3.computations.rqtl2.write_to_csv")
def test_generate_rqtl2_files(mock_write_to_csv):
    """Test for generating rqtl2 files from set of inputs"""

    mock_write_to_csv.side_effect = (
        "/tmp/workspace/geno_file.csv",
        "/tmp/workspace/pheno_file.csv"
    )
    data = {"crosstype": "riself",
            "geno_data": [{"NAME": "Ge_code_1"}],
            "pheno_data":  [{"NAME": "14343_at"}],
            "alleles": ["L", "C"],
            "geno_codes": {
                "L": 1,
                "C": 2
            },
            "na.strings": ["-", "NA"]
            }

    test_results = generate_rqtl2_files(data, "/tmp/workspace")
    expected_results = {"geno_file": "/tmp/workspace/geno_file.csv",
                        "pheno_file": "/tmp/workspace/pheno_file.csv",
                        **data
                        }
    assert test_results == expected_results

    # assert data is written to the csv
    expected_calls = [mock.call(
        "/tmp/workspace",
        "geno_file.csv",
        [{"NAME": "Ge_code_1"}]
    ),
        mock.call(
        "/tmp/workspace",
        "pheno_file.csv",
        [{"NAME": "14343_at"}]
    )]
    mock_write_to_csv.assert_has_calls(expected_calls)


@pytest.mark.unit_test
def test_validate_required_keys():
    """Test to validate required keys are in a dataset"""
    required_keys = ["geno_data", "pheno_data", "geno_codes"]
    assert ((False,
            "Required key(s) missing: geno_data, pheno_data, geno_codes")
            == validate_required_keys(required_keys, {})
            )
    assert ((True,
            "")
            == validate_required_keys(required_keys, {
                "geno_data": [],
                "pheno_data": [],
                "geno_codes": {}
            })
            )


@pytest.mark.unit_test
def test_compose_rqtl2_cmd():
    """Test for composing rqtl2 command"""
    input_file = "/tmp/575732e-691e-49e5-8d82-30c564927c95/input_file.json"
    output_file = "/tmp/575732e-691e-49e5-8d82-30c564927c95/output_file.json"
    directory = "/tmp/575732e-691e-49e5-8d82-30c564927c95"
    expected_results = f"Rscript /rqtl2_wrapper.R --input_file {input_file} --directory {directory} --output_file {output_file} --nperm 12 --threshold 0.05 --cores 1"

    # test for using default configs
    assert compose_rqtl2_cmd(rqtl_path="/rqtl2_wrapper.R",
                             input_file=input_file,
                             output_file=output_file,
                             workspace_dir=directory,
                             data={
                                 "nperm": 12,
                                 "threshold": 0.05
                             },
                             config={}) == expected_results

    # test for default permutation  and threshold and  custom configs
    expected_results = f"/bin/rscript /rqtl2_wrapper.R --input_file {input_file} --directory {directory} --output_file {output_file} --nperm 0 --threshold 1 --cores 12"
    assert (compose_rqtl2_cmd(rqtl_path="/rqtl2_wrapper.R",
                              input_file=input_file,
                              output_file=output_file,
                              workspace_dir=directory,
                              data={},
                              config={"MULTIPROCESSOR_PROCS": 12, "RSCRIPT": "/bin/rscript"})
            == expected_results)


@pytest.mark.unit_test
@mock.patch("gn3.computations.rqtl2.os.makedirs")
@mock.patch("gn3.computations.rqtl2.create_file")
@mock.patch("gn3.computations.rqtl2.uuid")
def test_preparing_rqtl_files(mock_uuid, mock_create_file, mock_mkdir):
    """test to create required rqtl files"""
    mock_create_file.return_value = None
    mock_mkdir.return_value = None
    mock_uuid.uuid4.return_value = "2fc75611-1524-418e-970f-67f94ea09846"
    assert (
        (
            "/tmp/2fc75611-1524-418e-970f-67f94ea09846",
            "/tmp/2fc75611-1524-418e-970f-67f94ea09846/rqtl2-input-2fc75611-1524-418e-970f-67f94ea09846.json",
            "/tmp/2fc75611-1524-418e-970f-67f94ea09846/rqtl2-output-2fc75611-1524-418e-970f-67f94ea09846.json",
            "/tmp/rqtl2-log-2fc75611-1524-418e-970f-67f94ea09846"
        ) == prepare_files(tmpdir="/tmp/")
    )
    # assert method to create files is called
    expected_calls = [mock.call("/tmp/2fc75611-1524-418e-970f-67f94ea09846/rqtl2-input-2fc75611-1524-418e-970f-67f94ea09846.json"),
                      mock.call(
                          "/tmp/2fc75611-1524-418e-970f-67f94ea09846/rqtl2-output-2fc75611-1524-418e-970f-67f94ea09846.json"),
                      mock.call("/tmp/rqtl2-log-2fc75611-1524-418e-970f-67f94ea09846")]
    mock_create_file.assert_has_calls(expected_calls)
