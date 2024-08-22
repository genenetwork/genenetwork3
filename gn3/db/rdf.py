"""RDF utilities

This module is a collection of functions that handle SPARQL queries.

"""
import json

from SPARQLWrapper import SPARQLWrapper
from pyld import jsonld  # type: ignore
from gn3.db.constants import (
    RDF_PREFIXES
)


def sparql_construct_query(query: str, endpoint: str) -> dict:
    """Query virtuoso using a CONSTRUCT query and return a json-ld
    dictionary"""
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    results = sparql.queryAndConvert()
    return json.loads(results.serialize(format="json-ld"))  # type: ignore


def query_frame_and_compact(query: str, context: dict, endpoint: str) -> dict:
    """Frame and then compact the results given a context"""
    results = sparql_construct_query(query, endpoint)
    if not results:
        return {}
    return jsonld.compact(jsonld.frame(results, context), context)


def query_and_compact(query: str, context: dict, endpoint: str) -> dict:
    """Compact the results given a context"""
    results = sparql_construct_query(query, endpoint)
    if not results:
        return {}
    return jsonld.compact(results, context)


def query_and_frame(query: str, context: dict, endpoint: str) -> dict:
    """Frame the results given a context"""
    results = sparql_construct_query(query, endpoint)
    if not results:
        return {}
    return jsonld.frame(results, context)
