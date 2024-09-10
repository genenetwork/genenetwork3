"""Tests for gn3/db/rdf/wiki.py"""

import pytest

from gn3.db.rdf.wiki import __sanitize_result


@pytest.mark.unit_test
@pytest.mark.parametrize(
    ("result", "expected"),
    (
        (
            {
                "categories": "",
                "comment": "comment",
                "created": "2006-12-23 17:19:14",
                "email": "XXX@XXX.edu",
                "initial": "KMz",
                "pubmed_ids": "",
                "reason": "add",
                "species": "mouse",
                "symbol": "Sfrs3",
                "version": 0,
                "web_url": "",
            },
            {
                "categories": [],
                "comment": "comment",
                "created": "2006-12-23 17:19:14",
                "email": "XXX@XXX.edu",
                "initial": "KMz",
                "pubmed_ids": [],
                "reason": "add",
                "species": "mouse",
                "symbol": "Sfrs3",
                "version": 0,
                "web_url": "",
            },
        ),
        (
            {
                "categories": "some-category",
                "comment": "comment",
                "created": "2006-12-23 17:19:14",
                "email": "XXX@XXX.edu",
                "initial": "KMz",
                "pubmed_ids": "",
                "reason": "add",
                "species": "mouse",
                "symbol": "Sfrs3",
                "version": 0,
                "web_url": "",
            },
            {
                "categories": ["some-category"],
                "comment": "comment",
                "created": "2006-12-23 17:19:14",
                "email": "XXX@XXX.edu",
                "initial": "KMz",
                "pubmed_ids": [],
                "reason": "add",
                "species": "mouse",
                "symbol": "Sfrs3",
                "version": 0,
                "web_url": "",
            },
        ),
        (
            {
                "categories": "",
                "comment": "comment",
                "created": "2006-12-23 17:19:14",
                "email": "XXX@XXX.edu",
                "initial": "KMz",
                "pubmed_ids": "21",
                "reason": "add",
                "species": "mouse",
                "symbol": "Sfrs3",
                "version": 0,
                "web_url": "",
            },
            {
                "categories": [],
                "comment": "comment",
                "created": "2006-12-23 17:19:14",
                "email": "XXX@XXX.edu",
                "initial": "KMz",
                "pubmed_ids": [21],
                "reason": "add",
                "species": "mouse",
                "symbol": "Sfrs3",
                "version": 0,
                "web_url": "",
            },
        ),
        (
            {
                "categories": "",
                "comment": "comment",
                "created": "2006-12-23 17:19:14",
                "email": "XXX@XXX.edu",
                "initial": "KMz",
                "pubmed_ids": 21,
                "reason": "add",
                "species": "mouse",
                "symbol": "Sfrs3",
                "version": 0,
                "web_url": "",
            },
            {
                "categories": [],
                "comment": "comment",
                "created": "2006-12-23 17:19:14",
                "email": "XXX@XXX.edu",
                "initial": "KMz",
                "pubmed_ids": [21],
                "reason": "add",
                "species": "mouse",
                "symbol": "Sfrs3",
                "version": 0,
                "web_url": "",
            },
        ),
        (
            {
                "categories": "",
                "comment": "comment",
                "created": "2006-12-23 17:19:14",
                "email": "XXX@XXX.edu",
                "initial": "KMz",
                "pubmed_ids": [21, 22],
                "reason": "add",
                "species": "mouse",
                "symbol": "Sfrs3",
                "version": 0,
                "web_url": "",
            },
            {
                "categories": [],
                "comment": "comment",
                "created": "2006-12-23 17:19:14",
                "email": "XXX@XXX.edu",
                "initial": "KMz",
                "pubmed_ids": [21, 22],
                "reason": "add",
                "species": "mouse",
                "symbol": "Sfrs3",
                "version": 0,
                "web_url": "",
            },
        ),
        ({}, {}),
    ),
)
def test_sanitize_result(result, expected):
    """Test that the JSON-LD result is sanitized correctly"""
    assert __sanitize_result(result) == expected
