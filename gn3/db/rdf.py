"""RDF utilities

This module is a collection of functions that handle SPARQL queries.

"""
import json

from SPARQLWrapper import SPARQLWrapper
from pyld import jsonld  # type: ignore


PREFIXES = {
    "dcat": "http://www.w3.org/ns/dcat#",
    "dct": "http://purl.org/dc/terms/",
    "ex": "http://example.org/stuff/1.0/",
    "fabio": "http://purl.org/spar/fabio/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "generif": "http://www.ncbi.nlm.nih.gov/gene?cmd=Retrieve&dopt=Graphics&list_uids=",
    "genotype": "http://genenetwork.org/genotype/",
    "gn": "http://genenetwork.org/id/",
    "gnc": "http://genenetwork.org/category/",
    "gnt": "http://genenetwork.org/term/",
    "owl": "http://www.w3.org/2002/07/owl#",
    "phenotype": "http://genenetwork.org/phenotype/",
    "prism": "http://prismstandard.org/namespaces/basic/2.0/",
    "publication": "http://genenetwork.org/publication/",
    "pubmed": "http://rdf.ncbi.nlm.nih.gov/pubmed/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "taxon": "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=",
    "up": "http://purl.uniprot.org/core/",
    "xkos": "http://rdf-vocabulary.ddialliance.org/xkos#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}


RDF_PREFIXES = "\n".join([f"PREFIX {key}: <{value}>"
                          for key, value in PREFIXES.items()])


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
