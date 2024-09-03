"""Test cases for procedures defined in llms """
import pytest
from gn3.llms.process import parse_context
from gn3.llms.process import format_bibliography_info


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

@pytest.mark.unit_test
def test_format_bib_info():
    mock_fahamu_bib_info = [
         {
             "author": "J.m",
             "firstName": "john",
             "title": "Genes and aging",
             "year": 2013,
             "doi": "https://Articles.com/12231"
         },
         "2019-Roy-Evaluation of Sirtuin-3 probe quality and co-expressed genes",
         "2015 - Differential regional and cellular distribution of TFF3 peptide in the human brain.txt"]
    expected_result = [
        "J.m.Genes and aging.2013.https://Articles.com/12231 ",
        "2019-Roy-Evaluation of Sirtuin-3 probe quality and co-expressed genes",
        "2015 - Differential regional and cellular distribution of TFF3 peptide in the human brain"
    ]

    assert all([format_bibliography_info(data) == expected
                for data, expected
                in zip(mock_fahamu_bib_info, expected_result)])
