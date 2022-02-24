from gn3.csvcmp import csv_diff
from gn3.csvcmp import fill_csv
from gn3.csvcmp import remove_insignificant_edits

import pytest


@pytest.mark.unit_test
def test_fill_csv():
    test_input = """
Strain Name,Value,SE,Count
BXD1,18,x,0
BXD12,16,x,x
BXD14,15,x,x
BXD15,14,x,x
"""
    expected_output = """Strain Name,Value,SE,Count,Sex
BXD1,18,x,0,x
BXD12,16,x,x,x
BXD14,15,x,x,x
BXD15,14,x,x,x"""
    assert(fill_csv(test_input, width=5, value="x"))

@pytest.mark.unit_test
def test_remove_insignificant_data():
    diff_data = {
        'Additions': [],
        'Deletions': [],
        'Modifications': [
            {'Current': '1.000001,3', 'Original': '1,3'},
            {'Current': '1,3', 'Original': '1.000001,3'},
            {'Current': '2.000001,3', 'Original': '2,2'},
            {'Current': '1.01,3', 'Original': '1,2'}
        ]
    }
    expected_json = {
        'Additions': [],
        'Deletions': [],
        'Modifications': [
            {'Current': '2,3', 'Original': '2,2'},
            {'Current': '1.01,3', 'Original': '1,2'}
        ]
    }
    assert (remove_insignificant_edits(diff_data) ==
            expected_json)


@pytest.mark.unit_test
def test_csv_diff():
    test_results = csv_diff(base_csv="a,b\n1,2\n",
                            delta_csv="a,b\n1,3")
    _json = {
        'Additions': [],
        'Deletions': [],
        'Modifications': [{'Current': '1,3', 'Original': '1,2'}]
    }
    assert(test_results.get("code") == 0 and
           test_results.get("output") == _json)