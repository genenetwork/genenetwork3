"""Tests for gn3/db/rdf/wiki.py"""
from unittest import TestCase

import pytest
import os

from gn3.db.rdf.wiki import (
    __sanitize_result,
    get_wiki_entries_by_symbol,
    get_comment_history,
    update_wiki_comment,
)


GRAPH = "<http://cd-test.genenetwork.org>"


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


@pytest.mark.rdf
def test_get_wiki_entries_by_symbol():
    """Test that wiki entries are fetched correctly by symbol"""
    result = get_wiki_entries_by_symbol(
        symbol="ckb",
        sparql_uri=os.environ.get("SPARQL_ENDPOINT", "http://localhost:9082/sparql"),
        graph=GRAPH,
    )
    expected = {
        "@context": {
            "categories": "gnt:belongsToCategory",
            "comment": "rdfs:comment",
            "created": "dct:created",
            "data": "@graph",
            "dct": "http://purl.org/dc/terms/",
            "email": "foaf:mbox",
            "foaf": "http://xmlns.com/foaf/0.1/",
            "gn": "http://genenetwork.org/id/",
            "gnc": "http://genenetwork.org/category/",
            "gnt": "http://genenetwork.org/term/",
            "id": "dct:identifier",
            "initial": "gnt:initial",
            "pubmed_ids": "dct:references",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "reason": "gnt:reason",
            "species": "gnt:species",
            "symbol": "rdfs:label",
            "type": "@type",
            "version": "gnt:hasVersion",
            "web_url": "foaf:homepage",
        },
        "data": [
            {
                "@id": "gn:wiki-1106-0",
                "categories": [],
                "comment": "high similarities on four locations on three different chromosomes",
                "created": "2007-01-16 10:06:34",
                "email": "XXX@XXX.com",
                "id": 1106,
                "initial": "dcc",
                "pubmed_ids": [],
                "reason": "",
                "species": "mouse",
                "symbol": "Ckb",
                "version": 0,
                "web_url": "",
            },
            {
                "@id": "gn:wiki-5006-0",
                "categories": [
                    "Genetic variation and alleles",
                    "Interactions: mRNA, proteins, other molecules",
                ],
                "comment": "Strong cis eQTL in brain RNA-seq data (LRS of 29 high B allele). Highly expressed in almost all neurons (not just interneurons). Trans targets of CKB include striatin (STRN) and C1QL3 (CTRP13).",
                "created": "2012-11-11 10:37:11",
                "email": "XXX@XXX.com",
                "id": 5006,
                "initial": "",
                "pubmed_ids": [],
                "reason": "",
                "species": "mouse",
                "symbol": "Ckb",
                "version": 0,
                "web_url": "",
            },
        ],
    }
    TestCase().assertDictEqual(result, expected)


@pytest.mark.rdf
def test_get_comment_history():
    result = get_comment_history(
        comment_id=1158,
        sparql_uri=os.environ.get("SPARQL_ENDPOINT", "http://localhost:9082/sparql"),
        graph=GRAPH,
    )
    expected = {
        "@context": {
            "categories": "gnt:belongsToCategory",
            "comment": "rdfs:comment",
            "created": "dct:created",
            "data": "@graph",
            "dct": "http://purl.org/dc/terms/",
            "email": "foaf:mbox",
            "foaf": "http://xmlns.com/foaf/0.1/",
            "gn": "http://genenetwork.org/id/",
            "gnc": "http://genenetwork.org/category/",
            "gnt": "http://genenetwork.org/term/",
            "id": "dct:identifier",
            "initial": "gnt:initial",
            "pubmed_ids": "dct:references",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "reason": "gnt:reason",
            "species": "gnt:species",
            "symbol": "rdfs:label",
            "type": "@type",
            "version": "gnt:hasVersion",
            "web_url": "foaf:homepage",
        },
        "data": [
            {
                "@id": "gn:wiki-1158-2",
                "categories": [
                    "Probes and probe sets",
                    "Transcriptional and translation control",
                ],
                "comment": "Validated strong cis-QTL in CNS using allele-specific expression (ASE) SNaPshot assay. Possible 3' UTR variants.",
                "created": "2007-04-05 09:11:05",
                "email": "XXX@XXX.com",
                "initial": "dcc",
                "pubmed_ids": [],
                "reason": "new data",
                "species": "mouse",
                "symbol": "Lpl",
                "version": 2,
                "web_url": "",
            },
            {
                "@id": "gn:wiki-1158-1",
                "categories": [
                    "Probes and probe sets",
                    "Transcriptional and translation control",
                ],
                "comment": "putative 3' UTR variants",
                "created": "2007-02-09 09:23:40",
                "email": "XXX@XXX.com",
                "initial": "dcc",
                "reason": "",
                "pubmed_ids": [],
                "species": "mouse",
                "symbol": "Lpl",
                "version": 1,
                "web_url": "",
            },
            {
                "@id": "gn:wiki-1158-0",
                "categories": [
                    "Probes and probe sets",
                    "Transcriptional and translation control",
                ],
                "comment": "Validated strong cis-QTL in CNS using allele-specific expression (ASE) SNaPshot assay (Daniel Ciobanu and al., 2007). Possible 3' UTR variants.",
                "created": "2007-05-08 14:46:07",
                "email": "XXX@XXX.com",
                "initial": "dcc",
                "pubmed_ids": [],
                "reason": "addition",
                "species": "mouse",
                "symbol": "Lpl",
                "version": 0,
                "web_url": "",
            },
        ],
    }
    # breakpoint()
    TestCase().assertDictEqual(result, expected)


@pytest.mark.rdf
def test_update_wiki_comment(rdf_setup):
    """Test that a comment is updated correctly"""
    response = update_wiki_comment(
        insert_dict={
            "Id": 230,
            "symbol": "Shh",
            "PubMed_ID": "2 3 4",
            "email": "test@test.com",
            "comment": "Updated comment",
            "createtime": "2007-01-16 11:06:34",
            "weburl": "http://some-website.com",
            "initial": "BMK",
            "reason": "Testing",
            "versionId": 3,
            "species": "mouse",
            "categories": [],
        },
        sparql_user=SPARQL_CONF["sparql_user"],
        sparql_password=SPARQL_CONF["sparql_password"],
        sparql_auth_uri=SPARQL_CONF["sparql_auth_uri"],
        graph=GRAPH,
    )
    updated_history = get_comment_history(
        comment_id=230,
        sparql_uri=SPARQL_CONF["sparql_endpoint"],
        graph=GRAPH,
    )["data"]
    assert len(updated_history) == 4
    TestCase().assertDictEqual(updated_history[0], {
        "@id": "gn:wiki-230-3",
        "categories": [],
        "comment": "Updated comment",
        "created": "2007-01-16 11:06:34",
        "email": "test@test.com",
        "initial": "BMK",
        "pubmed_ids": [2, 3, 4],
        "reason": "Testing",
        "species": "mouse",
        "symbol": "Shh",
        "version": 3,
        "web_url": "http://some-website.com",
    })
