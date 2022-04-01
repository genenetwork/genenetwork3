"""Tests for gn3.csvcmp"""
import pytest

from gn3.csvcmp import clean_csv_text
from gn3.csvcmp import csv_diff
from gn3.csvcmp import extract_invalid_csv_headers
from gn3.csvcmp import extract_strain_name
from gn3.csvcmp import fill_csv
from gn3.csvcmp import get_allowable_sampledata_headers
from gn3.csvcmp import remove_insignificant_edits


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
    assert csv_diff(base_csv="a,b \n1,2\n", delta_csv="a,b\n1,3") == {
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
        "Modifications": [
            {"Current": "BXD12,16,x,x,1", "Original": "BXD12,16,x,x,x"}
        ],
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
        extract_strain_name(
            csv_header="Strain Name,Value,SE,Count", data="BXD1,18,x,0"
        )
        == "BXD1"
    )


@pytest.mark.unit_test
def test_get_allowable_csv_headers(mocker):
    """Test that all the csv headers are fetched properly"""
    mock_conn = mocker.MagicMock()
    expected_values = [
        "Strain Name",
        "Value",
        "SE",
        "Count",
        "Condition",
        "Tissue",
        "Sex",
        "Age",
        "Ethn.",
        "PMI (hrs)",
        "pH",
        "Color",
    ]
    with mock_conn.cursor() as cursor:
        cursor.fetchall.return_value = (
            ("Condition",),
            ("Tissue",),
            ("Sex",),
            ("Age",),
            ("Ethn.",),
            ("PMI (hrs)",),
            ("pH",),
            ("Color",),
        )
        assert get_allowable_sampledata_headers(mock_conn) == expected_values
        cursor.execute.assert_called_once_with(
            "SELECT Name from CaseAttribute"
        )


@pytest.mark.unit_test
def test_extract_invalid_csv_headers_with_some_wrong_headers():
    """Test that invalid column headers are extracted correctly from a csv
    string"""
    allowed_headers = [
        "Strain Name",
        "Value",
        "SE",
        "Count",
        "Condition",
        "Tissue",
        "Sex",
        "Age",
        "Ethn.",
        "PMI (hrs)",
        "pH",
        "Color",
    ]

    csv_text = "Strain Name, Value, SE, Colour"
    assert extract_invalid_csv_headers(allowed_headers, csv_text) == ["Colour"]


@pytest.mark.unit_test
def test_clean_csv():
    """Test that csv text input is cleaned properly"""
    csv_text = """
Strain Name,Value,SE,Count 
BXD1,18,x ,0
BXD12, 16,x,x
BXD14,15 ,x,x
BXD15,14,x,
"""
    expected_csv = """Strain Name,Value,SE,Count
BXD1,18,x,0
BXD12,16,x,x
BXD14,15,x,x
BXD15,14,x,"""

    assert clean_csv_text(csv_text) == expected_csv
    assert clean_csv_text("a,b \n1,2\n") == "a,b\n1,2"
