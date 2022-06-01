import json
import os
import pytest

from gn3.computations.rust_correlation import CORRELATION_COMMAND
from gn3.computations.rust_correlation import generate_json_file
from gn3.computations.rust_correlation import generate_input_files
from gn3.computations.rust_correlation import run_correlation
from gn3.computations.rust_correlation import parse_correlation_output


@pytest.mark.unit_test
def test_run_correlation():
    """test calling rusts' correlation """

    pass


@pytest.mark.unit_test
def test_generate_input():
    """test generating text files"""

    test_dataset = [
        "14_at,12.1,14.1,None",
        "15_at,12.2,14.1,None",
        "17_at,12.1,14.1,11.4"

    ]

    (tmpdir, tmp_file) = generate_input_files(test_dataset, output_dir="/tmp")

    with open(tmp_file, "r") as file_reader:
        test_results = [line.rstrip() for line in file_reader]

    os.remove(tmp_file)

    assert test_results == test_dataset


@pytest.mark.unit_test
def test_json_file():

    json_dict = {"tmp_dir": "/tmp/correlation",

                 "tmp_file": "/data.txt",
                 "method": "pearson",
                 "file_path": "/data.txt",
                 "x_vals": "12.1,11.3,16.5,7.5,3.2",
                 "file_delimiter": ","}
    tmp_file = generate_json_file(**json_dict)

    with open(tmp_file, "r+") as file_reader:
        results = json.load(file_reader)

    assert results == {
        "method": "pearson",
        "file_path": "/data.txt",
        "x_vals": "12.1,11.3,16.5,7.5,3.2",
        "file_delimiter": ","}


@pytest.mark.unit_test
def test_kwargs():
    def rt(**kwargs):
        return kwargs

    assert rt(**{"name": "tt", "age": 12}) == {"name": "tt", "age": 12}


@pytest.mark.unit_test
def test_parse_results():

    raw_data = [
        ["63.62", "0.97", "0.00"],
        ["19", "-0.96", "0.22"],
        ["77.92", "-0.94", "0.31"],
        ["84.04", "0.94", "0.11"],
        ["23", "-0.91", "0.11"]
    ]

    expected_results = [{"trait_name": name, "corr_coeff": corr,
                         "p_val": pval} for (name, corr, pval) in raw_data]

    assert parse_correlation_output(
        "tests/unit/computations/data/correlation/sorted_results.txt") == expected_results
