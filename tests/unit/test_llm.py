"""Test cases for procedures defined in llms """
# pylint: disable=C0301
# pylint: disable=W0613
from datetime import datetime, timedelta
from unittest.mock import patch
from unittest.mock import MagicMock

import pytest
from gn3.llms.process import fetch_pubmed
from gn3.llms.process import parse_context
from gn3.llms.process import format_bibliography_info
from gn3.llms.errors import LLMError
from gn3.api.llm  import clean_query
from gn3.api.llm  import is_verified_anonymous_user
from gn3.api.llm  import is_valid_address
from gn3.api.llm  import check_rate_limiter


FAKE_NOW = datetime(2025, 1, 1, 12, 0, 0)
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


@pytest.mark.unit_test
def test_is_verified_anonymous_user():
    """Test function for verifying anonymous user metadata"""
    assert is_verified_anonymous_user({}) is False
    assert is_verified_anonymous_user({"Anonymous-Id" : "qws2121dwsdwdwe",
                                        "Anonymous-Status" : "verified"}) is True

@pytest.mark.unit_test
def test_is_valid_address() :
    """Test function checks if is a valid ip address is valid"""
    assert  is_valid_address("invalid_ip") is False
    assert is_valid_address("127.0.0.1") is True


@patch("gn3.api.llm.datetime")
@patch("gn3.api.llm.db.connection")
@patch("gn3.api.llm.is_valid_address", return_value=True)
@pytest.mark.unit_test
def test_first_time_visitor(mock_is_valid, mock_db_conn, mock_datetime):
    """Test rate limiting for first-time visitor"""
    mock_datetime.utcnow.return_value = FAKE_NOW
    mock_datetime.strptime = datetime.strptime  # keep real one
    mock_datetime.strftime = datetime.strftime  # keep real one

    # Set up DB mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_db_conn.return_value = mock_conn

    result = check_rate_limiter("127.0.0.1", "test/llm.db", "Chromosome x")
    assert result is True
    mock_cursor.execute.assert_any_call("""
                INSERT INTO Limiter(identifier, tokens, expiry_time)
                VALUES (?, ?, ?)
            """, ("127.0.0.1", 4, "2025-01-01 12:24:00"))


@patch("gn3.api.llm.datetime")
@patch("gn3.api.llm.db.connection")
@patch("gn3.api.llm.is_valid_address", return_value=True)
@pytest.mark.unit_test
def test_visitor_at_limit(mock_is_valid, mock_db_conn, mock_datetime):
    """Test rate limiting for Visitor at limit"""
    mock_datetime.utcnow.return_value = FAKE_NOW
    mock_datetime.strptime = datetime.strptime  # keep real one
    mock_datetime.strftime = datetime.strftime

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    fake_expiry = (FAKE_NOW + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    mock_cursor.fetchone.return_value = (0, fake_expiry) #token returned are 0
    mock_db_conn.return_value = mock_conn
    with pytest.raises(LLMError) as exc_info:
        check_rate_limiter("127.0.0.1", "test/llm.db", "Chromosome x")
    # assert llm error with correct message is raised
    assert exc_info.value.args == ('Rate limit exceeded. Please try again later.', 'Chromosome x')


@patch("gn3.api.llm.datetime")
@patch("gn3.api.llm.db.connection")
@patch("gn3.api.llm.is_valid_address", return_value=True)
@pytest.mark.unit_test
def test_visitor_with_tokens(mock_is_valid, mock_db_conn, mock_datetime):
    """Test rate limiting for user with valid tokens"""

    mock_datetime.utcnow.return_value = FAKE_NOW
    mock_datetime.strptime = datetime.strptime  # Use real versions
    mock_datetime.strftime = datetime.strftime

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    fake_expiry = (FAKE_NOW + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    mock_cursor.fetchone.return_value = (3, fake_expiry)  # Simulate 3 tokens

    mock_db_conn.return_value = mock_conn

    results = check_rate_limiter("127.0.0.1", "test/llm.db", "Chromosome x")
    assert results is True
    mock_cursor.execute.assert_any_call("""
                        UPDATE Limiter
                        SET tokens = tokens - 1
                        WHERE identifier = ? AND tokens > 0
                    """, ("127.0.0.1",))

@patch("gn3.api.llm.datetime")
@patch("gn3.api.llm.db.connection")
@patch("gn3.api.llm.is_valid_address", return_value=True)
@pytest.mark.unit_test
def test_visitor_token_expired(mock_is_valid, mock_db_conn, mock_datetime):
    """Test rate limiting for expired tokens"""

    mock_datetime.utcnow.return_value = FAKE_NOW
    mock_datetime.strptime = datetime.strptime
    mock_datetime.strftime = datetime.strftime
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    fake_expiry = (FAKE_NOW - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    mock_cursor.fetchone.return_value = (3, fake_expiry)  # Simulate 3 tokens
    mock_db_conn.return_value = mock_conn

    result = check_rate_limiter("127.0.0.1", "test/llm.db", "Chromosome x")
    assert result is True
    mock_cursor.execute.assert_any_call("""
                    UPDATE Limiter
                    SET tokens = ?, expiry_time = ?
                    WHERE identifier = ?
                """, (4, "2025-01-01 12:24:00", "127.0.0.1"))
