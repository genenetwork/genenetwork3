"""RDF utilities

This module is a collection of functions that handle SPARQL queries.

"""
from typing import Tuple
from string import Template
from urllib.parse import unquote
from urllib.parse import urlparse

from SPARQLWrapper import JSON, SPARQLWrapper

from gn3.monads import MonadicDict

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


RDF_PREFIXES = "\n".join([f"PREFIX {key}: <{value}>"for key, value in PREFIXES.items()])


def sparql_query(
        sparql_conn: SPARQLWrapper, query: str,
) -> Tuple[MonadicDict, ...]:
    """Run a SPARQL query and return the bound variables."""
    def __add_value_to_dict(key, value, my_dict):
        _values = set()
        if key in my_dict:
            if isinstance(my_dict[key], list):
                _values = set(my_dict[key])
            else:
                _values = set([my_dict[key]])
            _values.add(value)
        if _values:
            return list(_values)
        return value

    sparql_conn.setQuery(query)
    sparql_conn.setReturnFormat(JSON)
    parsed_response: dict = {}
    results = sparql_conn.queryAndConvert()["results"]["bindings"]  # type: ignore
    if results:
        for result in results:
            if "s" in result:  # A CONSTRUCT
                key = result["p"]["value"]  # type: ignore
                value = result["o"]["value"]  # type: ignore
                parsed_response[key] = __add_value_to_dict(
                    key, value, parsed_response
                )
            elif "key" in result:  # A SELECT
                parsed_response[
                    result["key"]  # type: ignore
                ] = __add_value_to_dict(
                    result["key"], result["value"],  # type: ignore
                    parsed_response
                )
    return (MonadicDict(parsed_response),)


def get_url_local_name(string: str) -> str:
    """Get the last item after a '/" from a URL"""
    if string.startswith("http"):
        url = urlparse(string)
        return unquote(url.path).rpartition("/")[-1]
    return string
