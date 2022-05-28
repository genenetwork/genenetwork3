import pytest

from gn3.computations.rust_correlation import CORRELATION_COMMAND
from gn3.computations.rust_correlation import run_correlation
from gn3.computations.rust_correlation import parse_correlation_output


@pytest.mark.unit_test
def test_run_correlation():
    """test calling rusts' correlation """

    results = run_correlation(
        file_name="/home/kabui/correlation_rust/tests/data/sample_json_file.json", outputdir="/")

    assert results == "hello"


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
