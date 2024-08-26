"""RDF utilities

This module is a collection of functions that handle SPARQL queries.

"""
import json
from string import Template
from SPARQLWrapper import SPARQLWrapper
from pyld import jsonld  # type: ignore
from gn3.db.constants import (
    RDF_PREFIXES, BASE_CONTEXT
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
    return jsonld.compact(jsonld.frame(results, context), context)


def query_and_compact(query: str, context: dict, endpoint: str) -> dict:
    """Compact the results given a context"""
    results = sparql_construct_query(query, endpoint)
    return jsonld.compact(results, context)


def query_and_frame(query: str, context: dict, endpoint: str) -> dict:
    """Frame the results given a context"""
    results = sparql_construct_query(query, endpoint)
    return jsonld.frame(results, context)


def get_wiki_entries_by_symbol(symbol: str, sparql_uri: str) -> dict:
    """Fetch all the Wiki entries using the symbol"""
    # FIXME: Get the latest VersionId of a comment.
    query = Template("""
$prefix

CONSTRUCT {
    _:node rdfs:label '$symbol';
           gnt:reason ?reason ;
           gnt:species ?species ;
           dct:references ?pmid ;
           foaf:homepage ?weburl ;
           rdfs:comment ?wikientry ;
           foaf:mbox ?email ;
           gnt:initial ?usercode ;
           gnt:belongsToCategory ?category ;
           gnt:hasVersion ?versionId
} WHERE {
    ?symbolId rdfs:comment _:node ;
              rdfs:label '$symbol' .
    _:node rdf:type gnc:GNWikiEntry ;
           dct:hasVersion "0"^^xsd:int ;
           dct:hasVersion ?version ;
           rdfs:comment ?wikientry .
    OPTIONAL { _:node gnt:reason ?reason } .
    OPTIONAL {
        _:node gnt:belongsToSpecies ?speciesId .
        ?speciesId gnt:shortName ?species .
    } .
    OPTIONAL { _:node dct:references ?pubmedId . } .
    OPTIONAL { _:node foaf:homepage ?weburl . } .
    OPTIONAL { _:node gnt:initial ?usercode . } .
    OPTIONAL { _:node gnt:mbox ?email . } .
    OPTIONAL { _:node gnt:belongsToCategory ?category . }
    BIND (str(?version) AS ?versionId) .
    BIND (str(?pubmedId) AS ?pmid)
}
""").substitute(prefix=RDF_PREFIXES, symbol=symbol,)
    context = BASE_CONTEXT | {
        "foaf": "http://xmlns.com/foaf/0.1/",
        "dct": "http://purl.org/dc/terms/",
        "categories": "gnt:belongsToCategory",
        "web_url": "foaf:homepage",
        "version": "gnt:hasVersion",
        "symbol": "rdfs:label",
        "reason": "gnt:reason",
        "species": "gnt:species",
        "pubmed_id": "dct:references",
        "web_url": "foaf:homepage",
        "email": "foaf:mbox",
        "initial": "gnt:initial",
        "comment": "rdfs:comment"
    }
    results = query_frame_and_compact(
        query, context,
        sparql_uri
    )
    data = results.get("data")
    if not data:
        return results
    for result in data:
        if result.get("categories"):
            result["categories"] = [
                x.strip() for x in result.get("categories").split(";")]
    return results
