"""RDF utilities

This module is a collection of functions that handle SPARQL queries.

"""
from typing import Tuple
from string import Template
from urllib.parse import unquote
from urllib.parse import urlparse

from SPARQLWrapper import JSON, SPARQLWrapper
from pymonad.maybe import Just
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
PREFIX gn: <http://genenetwork.org/>

SELECT ?accession_id ?dataset_group ?status ?title ?geo_series ?specifics ?summary ?about_tissue
?about_platform ?about_data_processing ?notes ?experiment_design ?contributors ?citation ?acknowledgement
?platform_name ?tissue_name ?normalization_name ?species_name ?inbred_set_name
?name ?address ?city ?state ?zip ?phone ?email ?country ?homepage
WHERE {
  ?dataset gn:accessionId ?accession_id ;
           rdf:type gn:dataset ;
           gn:name "$name" .
  OPTIONAL { ?dataset gn:aboutDataProcessing ?about_data_processing } .
  OPTIONAL { ?dataset gn:aboutPlatform ?about_platform } .
  OPTIONAL { ?dataset gn:aboutTissue ?about_tissue } .
  OPTIONAL { ?dataset gn:acknowledgement ?acknowledgement } .
  OPTIONAL { ?dataset gn:citation ?citation } .
  OPTIONAL { ?dataset gn:contributors ?contributors } .
  OPTIONAL { ?dataset gn:datasetGroup ?dataset_group } .
  OPTIONAL { ?dataset gn:datasetStatus ?status } .
  OPTIONAL { ?dataset gn:experimentDesign ?experiment_design } .
  OPTIONAL { ?dataset gn:geoSeries ?geo_series } .
  OPTIONAL { ?dataset gn:notes ?notes } .
  OPTIONAL { ?dataset gn:specifics ?specifics } .
  OPTIONAL { ?dataset gn:summary ?summary } .
  OPTIONAL { ?dataset gn:title ?title } .
  OPTIONAL {
    ?dataset gn:normalization ?normalization .
    ?normalization gn:name ?normalization_name .
  } .
  OPTIONAL {
    ?dataset gn:datasetOfPlatform ?platform .
    ?platform gn:name ?platform_name .
  } .
  OPTIONAL {
    ?dataset gn:datasetOfTissue ?tissue .
    ?tissue gn:name ?tissue_name .
  } .
  OPTIONAL {
      ?dataset gn:datasetOfSpecies ?species ;
               gn:datasetOfInbredSet ?inbred_set .
      ?species gn:name ?species_name .
      ?inbred_set gn:name ?inbred_set_name .
  } .
  OPTIONAL {
      ?dataset gn:datasetOfInvestigator ?investigator .
           OPTIONAL { ?investigator foaf:name ?name . }
           OPTIONAL { ?investigator gn:address ?address . }
           OPTIONAL { ?investigator gn:city ?city . }
           OPTIONAL { ?investigator gn:state ?state . }
           OPTIONAL { ?investigator gn:zipCode ?zip . }
           OPTIONAL { ?investigator foaf:phone ?phone . }
           OPTIONAL { ?investigator foaf:mbox ?email . }
           OPTIONAL { ?investigator gn:country ?country . }
           OPTIONAL { ?investigator foaf:homepage ?homepage . }
  }
}
    """
    result: MonadicDict = MonadicDict()
    for key, value in sparql_query(
            sparql_conn,
            Template(__metadata_query).substitute(name=name)
    )[0].items():
        result[key] = value.bind(lambda x: Just(x["value"]))
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
