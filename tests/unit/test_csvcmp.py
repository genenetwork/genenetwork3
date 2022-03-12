"""Tests for gn3.csvcmp"""
import pytest

from gn3.csvcmp import csv_diff
from gn3.csvcmp import fill_csv
from gn3.csvcmp import remove_insignificant_edits
from gn3.csvcmp import extract_strain_name


@pytest.mark.unit_test
def test_fill_csv():
    """Test that filling a csv works properly"""
    test_input = """
Strain Name,Value,SE,Count,Sex
BXD1,18,x,0,
BXD12,16,x,x,
BXD14,15,x,x,
BXD15,14,x,x
"""
    expected_output = """Strain Name,Value,SE,Count,Sex
BXD1,18,x,0,x
BXD12,16,x,x,x
BXD14,15,x,x,x
BXD15,14,x,x,x"""
    assert fill_csv(test_input, width=5, value="x") == expected_output


@pytest.mark.unit_test
def test_remove_insignificant_data():
    """Test that values outside ε are removed/ ignored"""
    diff_data = {
        "Additions": [],
        "Deletions": [],
        "Modifications": [
            {"Current": "1.000001,3", "Original": "1,3"},
            {"Current": "1,3", "Original": "1.000001,3"},
            {"Current": "2.000001,3", "Original": "2,2"},
            {"Current": "1.01,3", "Original": "1,2"},
        ],
    }
    expected_json = {
        "Additions": [],
        "Deletions": [],
        "Modifications": [
            {"Current": "2,3", "Original": "2,2"},
            {"Current": "1.01,3", "Original": "1,2"},
        ],
    }
    assert remove_insignificant_edits(diff_data) == expected_json


@pytest.mark.unit_test
def test_csv_diff_same_columns():
    """Test csv diffing on data with the same number of columns"""
    assert csv_diff(base_csv="a,b\n1,2\n", delta_csv="a,b\n1,3") == {
        "Additions": [],
        "Deletions": [],
        "Columns": "",
        "Modifications": [{"Current": "1,3", "Original": "1,2"}],
    }


@pytest.mark.unit_test
def test_csv_diff_different_columns():
    """Test csv diffing on data with different columns"""
    base_csv = """
Strain Name,Value,SE,Count
BXD1,18,x,0
BXD12,16,x,x
BXD14,15,x,x
BXD15,14,x,x
"""
    delta_csv = """Strain Name,Value,SE,Count,Sex
BXD1,18,x,0
BXD12,16,x,x,1
BXD14,15,x,x
BXD15,14,x,x"""
    assert csv_diff(base_csv=base_csv, delta_csv=delta_csv) == {
        "Additions": [],
        "Columns": "Strain Name,Value,SE,Count,Sex",
        "Deletions": [],
        "Modifications": [{"Current": "BXD12,16,x,x,1", "Original": "BXD12,16,x,x,x"}],
    }


@pytest.mark.unit_test
def test_csv_diff_only_column_change():
    """Test csv diffing when only the column header change"""
    base_csv = """
Strain Name,Value,SE,Count
BXD1,18,x,0
BXD12,16,x,x
BXD14,15,x,x
BXD15,14,x,x
"""
    delta_csv = """Strain Name,Value,SE,Count,Sex
BXD1,18,x,0
BXD12,16,x,x
BXD14,15,x,x
BXD15,14,x,x
"""
    assert csv_diff(base_csv=base_csv, delta_csv=delta_csv) == {
        "Additions": [],
        "Deletions": [],
        "Modifications": [],
    }


@pytest.mark.unit_test
def test_extract_strain_name():
    """Test that the strain's name is extracted given a csv header"""
    assert (
        extract_strain_name(csv_header="Strain Name,Value,SE,Count", data="BXD1,18,x,0")
        == "BXD1"
    )
