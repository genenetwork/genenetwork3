# pylint: disable=unused-argument
"""Test cases for procedures defined in llms module"""
from dataclasses import dataclass
import pytest
from gn3.llms.process import get_gnqa
from gn3.llms.process import parse_context



@pytest.mark.unit_test
def test_parse_context():
    """test for parsing doc id context"""
    def mock_get_info(doc_id):
        return f"Info for {doc_id}"

    def mock_format_bib(doc_info):
        return f"Formatted Bibliography: {doc_info}"

    parsed_result = parse_context({
        "doc1": [{"text": "Summary 1"}, {"text": "Summary 2"}],
        "doc2": [{"text": "Summary 3"}, {"text": "Summary 4"}],
    }, mock_get_info, mock_format_bib)

    expected_result = [
        {
            "doc_id": "doc1",
            "bibInfo": "Formatted Bibliography: Info for doc1",
            "comboTxt": "\tSummary 1\tSummary 2",
        },
        {
            "doc_id": "doc2",
            "bibInfo": "Formatted Bibliography: Info for doc2",
            "comboTxt": "\tSummary 3\tSummary 4",
        },
    ]

    assert parsed_result == expected_result
