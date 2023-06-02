"""RDF utilities

This module is a collection of functions that handle SPARQL queries.

"""
from typing import Tuple
from string import Template
from urllib.parse import unquote
from urllib.parse import urlparse

from SPARQLWrapper import JSON, SPARQLWrapper
from pymonad.maybe import Just, Nothing

from gn3.monads import MonadicDict


RDF_PREFIXES = """PREFIX dct: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX generif: <http://www.ncbi.nlm.nih.gov/gene?cmd=Retrieve&dopt=Graphics&list_uids=>
PREFIX gn: <http://genenetwork.org/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX pubmed: <http://rdf.ncbi.nlm.nih.gov/pubmed/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX taxon: <http://purl.uniprot.org/taxonomy/>
PREFIX up: <http://purl.uniprot.org/core/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

"""


def sparql_query(
        sparql_conn: SPARQLWrapper, query: str
) -> Tuple[MonadicDict, ...]:
    """Run a SPARQL query and return the bound variables."""
    sparql_conn.setQuery(query)
    sparql_conn.setReturnFormat(JSON)
    results = sparql_conn.queryAndConvert()
    if _r := results["results"]["bindings"]:  # type: ignore
        return (*(MonadicDict(bindings) for bindings in _r),)  # type: ignore
    return (MonadicDict(),)


def strip_url(string: str) -> str:
    """Get the last item after a '/" from a URL"""
    if string.startswith("http"):
        url = urlparse(string)
        return unquote(url.path).rpartition("/")[-1]
    return string


def get_dataset_metadata(
        sparql_conn: SPARQLWrapper, name: str
) -> MonadicDict:
    """Return info about dataset with a given NAME"""
    __metadata_query = """
$prefix

CONSTRUCT {
    gn:dataset ?datasetTerm ?datasetValue .
    gn:dataset ?platformName ?platform_name .
    gn:dataset gn:normalization ?normalization .
    gn:dataset gn:investigatorName ?investigatorName .
    gn:dataset gn:investigatorWebUrl ?investigatorWebUrl .
    gn:dataset gn:tissueName ?tissueName .
} WHERE {
    ?subClass rdf:subClassOf gn:dataset .
    ?dataset rdf:type ?subclass ;
             gn:name "$name";
             ?datasetTerm ?datasetValue .
    OPTIONAL {
        ?dataset gn:datasetOfInvestigator ?investigator .
        ?investigator foaf:name ?investigatorName .
        ?investigator foaf:homepage ?investigatorWebUrl .
    } .
    OPTIONAL{
        ?dataset gn:normalization ?normalizationType .
        ?normalizationType gn:name ?normalization .
    } .
    OPTIONAL{
        ?dataset gn:datasetOfPlatform ?platform .
        ?platform gn:name ?platform_name .
    } .
    OPTIONAL{
        ?dataset gn:datasetOfTissue ?tissue .
        ?tissue gn:name ?tissueName .
    } .
    VALUES ?datasetTerm {
        dct:created gn:aboutCases gn:aboutDataProcessing gn:aboutPlatform
        gn:aboutTissue gn:accessionId gn:acknowledgment gn:citation
        gn:contributors gn:datasetGroup gn:datasetOfinvestigator
        gn:experimentDesign gn:geoSeries gn:name gn:notes
        gn:specifics gn:summary gn:title
    }
}
"""
    result: MonadicDict = MonadicDict()
    results = sparql_query(
        sparql_conn,
        Template(__metadata_query).substitute(prefix=RDF_PREFIXES, name=name),
    )
    for item in results:
        predicate = (item["p"]
                     .map(lambda x: x["value"]) # type: ignore
                     .map(strip_url))
        subject = (
            item["s"]
            .map(lambda x: x["value"]) # type: ignore
            .map(strip_url)
            .maybe(None, lambda x: x)
        )
        object_ = (item["o"]
                   .maybe(
                       Nothing,
                       lambda x: Just(x["value"])) # type: ignore
                   )
        if subject == "homepage":
            object_ = object_.map(strip_url) # type: ignore
        if _p := predicate.maybe(None, lambda x: x):  # type: ignore
            result[_p] = object_
    return result


def get_trait_metadata(
        sparql_conn: SPARQLWrapper,
        trait_name: str,
        dataset_name: str
):
    """Return metadata about a given trait"""
    __metadata_query = """
PREFIX gn: <http://genenetwork.org/>

SELECT strafter((str(?key)), "http://genenetwork.org/sampledata:") as ?key
    ?value WHERE {
    gn:sampledata_$trait_name gn:sampledata:dataset "$dataset_name" .
    gn:sampledata_$trait_name ?key ?value .
}
"""
    result: MonadicDict = MonadicDict()
    for _r in sparql_query(
            sparql_conn,
            Template(__metadata_query)
            .substitute(trait_name=trait_name,
                        dataset_name=dataset_name)
    ):
        _key = _r["key"].bind(lambda x: x["value"])  # type:ignore
        if _key:
            result[_key] = _r["value"].bind(lambda x: Just(x["value"]))  # type:ignore
    return result
