"""Test cases for procedures defined in llms """
# pylint: disable=C0301
import pytest
from gn3.llms.process import fetch_pubmed
from gn3.llms.process import parse_context
from gn3.llms.process import format_bibliography_info
from gn3.api.llm  import clean_query


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
    """Test for formatting bibliography info """
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

    assert all((format_bibliography_info(data) == expected
                for data, expected
                in zip(mock_fahamu_bib_info, expected_result)))


@pytest.mark.unit_test
def test_fetching_pubmed_info(monkeypatch):
    """Test for fetching and populating pubmed data with pubmed info"""
    def mock_load_file(_filename, _dir_path):
        return {
            "12121": {
                "Abstract": "items1",
                "Author": "A1"
            }
        }
    # patch the module with the mocked function

    monkeypatch.setattr("gn3.llms.process.load_file", mock_load_file)
    expected_results = [
        {
            "title": "Genes",
            "year": "2014",
            "doi": "https/article/genes/12121",
            "doc_id": "12121",
            "pubmed": {
                "Abstract": "items1",
                "Author": "A1"
            }
        },
        {
            "title": "Aging",
            "year": "2014",
            "doc_id": "12122"
        }
    ]

    data = [{
            "title": "Genes",
            "year": "2014",
            "doi": "https/article/genes/12121",
            "doc_id": "12121",
            },
            {
            "title": "Aging",
            "year": "2014",
            "doc_id": "12122"
            }]

    assert (fetch_pubmed(data, "/pubmed.json",  "data/")
            == expected_results)


@pytest.mark.unit_test
def test_clean_query():
    """Test function for cleaning up query"""
    assert clean_query("!what is genetics.") == "what is genetics"
    assert clean_query("hello test?") == "hello test"
    assert clean_query("  hello test with space?") == "hello test with space"
