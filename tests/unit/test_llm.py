"""Test cases for procedures defined in llms module"""
import pytest
from dataclasses import dataclass
from gn3.llms.process import get_gnqa
from gn3.llms.process import parse_context


@pytest.fixture
def context_data():
    return {
        "doc1": [{"text": "Summary 1"}, {"text": "Summary 2"}],
        "doc2": [{"text": "Summary 3"}, {"text": "Summary 4"}],
    }


@pytest.mark.unit_test
def test_parse_context(context_data):
    def mock_get_info(doc_id):
        return f"Info for {doc_id}"

    def mock_format_bib(doc_info):
        return f"Formatted Bibliography: {doc_info}"

    parsed_result = parse_context(context_data, mock_get_info, mock_format_bib)

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

@dataclass(frozen=True)
class MockResponse:
    text: str

    def __getattr__(self, name: str):
        return self.__dict__[f"_{name}"]

class MockGeneNetworkQAClient:
    def __init__(self, session, api_key):
        pass

    def ask(self, query, auth_token):
        # Simulate the ask method
        return MockResponse("Mock response"), "F400995EAFE104EA72A5927CE10C73B7"

    def get_answer(self, task_id):
        # Simulate the get_answer method
        return MockResponse("Mock answer"), 1


def mock_filter_response_text(text):
    """ method to simulate the filterResponseText method"""
    return {"data": {"answer": "Mock answer for what is a gene", "context": {}}}


def mock_parse_context(context, get_info_func, format_bib_func):
    """method to simulate the  parse context method"""
    return []


@pytest.mark.unit_test
def test_get_gnqa(monkeypatch):
    monkeypatch.setattr(
        "gn3.llms.process.GeneNetworkQAClient",
        MockGeneNetworkQAClient
    )

    monkeypatch.setattr(
        'gn3.llms.process.filter_response_text',
        mock_filter_response_text
    )
    monkeypatch.setattr(
        'gn3.llms.process.parse_context',
        mock_parse_context
    )

    query = "What is a gene"
    auth_token = "test_token"
    result = get_gnqa(query, auth_token)

    expected_result = (
        "F400995EAFE104EA72A5927CE10C73B7",
        'Mock answer for what is a gene',
        []
    )

    assert result == expected_result
