import pytest

from gn3.computations.rust_correlation import CORRELATION_COMMAND
from gn3.computations.rust_correlation import run_correlation


@pytest.mark.unit_test

def test_equality():
	"""initial test for sum """

	assert 4 == 4



@pytest.mark.unit_test

def test_run_correlation():
	"""test calling rusts' correlation """


	results =  run_correlation("./tests/data/sample_json_file.json")

	assert results == "hello"
