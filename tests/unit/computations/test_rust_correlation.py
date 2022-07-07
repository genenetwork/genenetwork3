"""gn3.computations.rust_correlation unittests"""

import json
import os
import pytest

from gn3.computations.rust_correlation import generate_json_file
from gn3.computations.rust_correlation import generate_input_files
from gn3.computations.rust_correlation import get_samples
from gn3.computations.rust_correlation import parse_correlation_output


@pytest.mark.unit_test
def test_generate_input():
    """test generating text files"""

    test_dataset = [
        "14_at,12.1,14.1,None",
        "15_at,12.2,14.1,None",
        "17_at,12.1,14.1,11.4"

    ]

    (_tmp_dir, tmp_file) = generate_input_files(test_dataset,
                                                output_dir="/tmp")

    with open(tmp_file, "r", encoding="utf-8") as file_reader:
        test_results = [line.rstrip() for line in file_reader]

    os.remove(tmp_file)

    assert test_results == test_dataset


# @pytest.mark.unit_test
def test_json_file():
    """test for generating json files """

    tmp_file = generate_json_file(tmp_dir="/tmp/correlation",
                                  tmp_file="/data.txt",
                                  method="pearson",
                                  x_vals="12.1,11.3,16.5,7.5,3.2",
                                  delimiter=",")

    with open(tmp_file, "r+", encoding="utf-8") as file_reader:
        results = json.load(file_reader)

    assert results == {
        "method": "pearson",
        "file_path": "/data.txt",
        "x_vals": "12.1,11.3,16.5,7.5,3.2",
        "file_delimiter": ","}


@pytest.mark.unit_test
def test_parse_results():
    """test for parsing file results"""

    raw_data = [
        ["63.62", "0.97", "0.00"],
        ["19", "-0.96", "0.22"],
        ["77.92", "-0.94", "0.31"],
        ["84.04", "0.94", "0.11"],
        ["23", "-0.91", "0.11"]
    ]

    raw_dict = [{trait: {
        "num_overlap":  00,
                "p_value": p_val}} for (trait, corr_coeff, p_val) in raw_data]

    assert (parse_correlation_output(
        "tests/unit/computations/data/correlation/sorted_results.txt",
        len(raw_data))
        == raw_dict)


@pytest.mark.unit_test
def test_get_samples_no_excluded():
    """test for getting sample data"""

    al_samples = {
        "BXD": "12.1",
        "BXD3": "16.1",
        "BXD4": " x",
        "BXD6": "1.1",
        "BXD5": "1.37",
        "BXD11": "1.91",
        "BXD31": "1.1"

    }

    base = [
        "BXD",
        "BXD4",
        "BXD7",
        "BXD31"
    ]

    assert get_samples(all_samples=al_samples,
                       base_samples=base,
                       excluded=[]) == {
        "BXD": 12.1,
        "BXD31": 1.1
    }


@pytest.mark.unit_test
def test_get_samples():
    """test for getting samples with exluded"""

    al_samples = {
        "BXD": "12.1",
        "BXD3": "16.1",
        "BXD4": " x",
        "BXD5": "1.1",
        "BXD6": "1.37",
        "BXD11": "1.91",
        "BXD31": "1.1"

    }

    assert get_samples(all_samples=al_samples,
                       base_samples=["BXD", "BXD4", "BXD5", "BXD6",
                                     "BXD11"
                                     ], excluded=["BXD", "BXD11"]), {
        "BXD5": 1.1,
        "BXD6": 1.37
    }
