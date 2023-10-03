"""RDF utilities

This module is a collection of functions that handle SPARQL queries.

"""
from typing import Tuple
from string import Template
from urllib.parse import unquote
from urllib.parse import urlparse

from SPARQLWrapper import JSON, SPARQLWrapper

from gn3.monads import MonadicDict


RDF_PREFIXES = """
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX ex: <http://example.org/stuff/1.0/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX generif: <http://www.ncbi.nlm.nih.gov/gene?cmd=Retrieve&dopt=Graphics&list_uids=>
PREFIX genotype: <http://genenetwork.org/genotype/>
PREFIX gn: <http://genenetwork.org/id/>
PREFIX gnc: <http://genenetwork.org/category/>
PREFIX gnt: <http://genenetwork.org/term/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX phenotype: <http://genenetwork.org/phenotype/>
PREFIX publication: <http://genenetwork.org/publication/>
PREFIX pubmed: <http://rdf.ncbi.nlm.nih.gov/pubmed/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX taxon: <https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=>
PREFIX up: <http://purl.uniprot.org/core/>
PREFIX xkos: <http://rdf-vocabulary.ddialliance.org/xkos#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""


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
                key = get_url_local_name(
                    result["p"]["value"]  # type: ignore
                )
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
    gn:dataset gn:organism ?speciesDisplayName .
    gn:dataset gn:organismUrl ?ncbiReference .
    gn:dataset gn:inbredSetName ?inbredSetName .
    gn:dataset gn:geoPlatformUrl ?geoPlatform .
    gn:dataset gn:platformName ?platform_name .
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
        ?dataset gn:datasetOfSpecies ?species .
        ?species gn:displayName ?speciesDisplayName .
        ?species gn:organism ?ncbiReference .
    } .
    OPTIONAL {
        ?dataset gn:datasetOfInbredSet ?inbredSet .
        ?inbredSet gn:binomialName ?inbredSetName .
        ?inbredSet gn:inbredSetOfSpecies ?species .
        ?species gn:displayName ?speciesDisplayName .
        ?species gn:organism ?ncbiReference .
    } .
    OPTIONAL{
        ?dataset gn:datasetOfPlatform ?platform .
        ?platform gn:name ?platform_name .
        ?platform gn:geoPlatform ?geoPlatform .
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
        gn:specifics gn:summary gn:title gn:publicationTitle
        gn:datasetStatusName gn:datasetOfOrganization
    }
}
"""
    response: MonadicDict = MonadicDict()
    for key, value in sparql_query(
            sparql_conn,
            Template(__metadata_query)
            .substitute(
                prefix=RDF_PREFIXES,
                name=name
            )
    )[0].items():
        response[key] = value
        if isinstance(value, str) and not (
                key.endswith("Url") or key == "geoSeries"
        ):
            response[key] = value.map(get_url_local_name)  # type: ignore
    return response


def get_publication_metadata(
        sparql_conn: SPARQLWrapper, name: str
):
    """Return info about a publication with a given NAME"""
    __metadata_query = """
$prefix

CONSTRUCT {
    gn:publication ?publicationTerm ?publicationValue .
    gn:publication ?predicate ?subject .
} WHERE {
    $name ?publicationTerm ?publicationValue .
    ?publication ?publicationTerm ?publicationValue .
    OPTIONAL {
       ?subject ?predicate ?publication .
    } .
    VALUES ?publicationTerm {
        gn:pubMedId gn:title gn:volume
        gn:abstract gn:pages gn:month gn:year gn:author
    }
    VALUES ?predicate {
        gn:phenotypeOfPublication
    }
}
"""
    response: MonadicDict = MonadicDict()
    for key, value in sparql_query(
            sparql_conn,
            Template(__metadata_query)
            .substitute(
                prefix=RDF_PREFIXES,
                name=name
            )
    )[0].items():
        response[key] = value
        if isinstance(value, str) and not key.endswith("pubMedId"):
            response[key] = value.map(get_url_local_name)  # type: ignore
    return response


def get_phenotype_metadata(
        sparql_conn: SPARQLWrapper, name: str
):
    """Return info about a phenotype with a given NAME"""
    __metadata_query = """
$prefix

CONSTRUCT {
    ?phenotype ?pPredicate ?pValue .
    ?phenotype ?publicationTerm ?publicationValue .
    ?phenotype gn:speciesName ?speciesName .
    ?phenotype gn:inbredSetName ?inbredSetBinomialName .
    ?phenotype gn:datasetName ?datasetFullName .
} WHERE {
    ?phenotype ?pPredicate ?pValue .
    OPTIONAL {
        ?phenotype gn:phenotypeOfPublication ?publication .
        ?publication ?publicationTerm ?publicationValue .
    } .
    OPTIONAL {
        ?phenotype gn:phenotypeOfDataset ?dataset .
        ?dataset gn:name ?datasetFullName .
        ?dataset gn:datasetOfInbredSet ?inbredSet .
        ?inbredSet gn:binomialName ?inbredSetBinomialName .
        ?inbredSet gn:inbredSetOfSpecies ?species .
        ?species gn:displayName ?speciesName .
    } .
    FILTER( ?phenotype = phenotype:$name ) .
    MINUS {
         ?phenotype rdf:type ?pValue .
    }
    MINUS {
         ?publication rdf:type ?publicationValue .
    }
}
"""
    result: MonadicDict = MonadicDict()
    for key, value in sparql_query(
            sparql_conn,
            Template(__metadata_query)
            .substitute(name=name,
                        prefix=RDF_PREFIXES)
    )[0].items():
        result[key] = value
    return result


def get_genotype_metadata(
        sparql_conn: SPARQLWrapper, name: str
):
    """Return info about a phenotype with a given NAME"""
    __metadata_query = """
$prefix

CONSTRUCT {
    ?genotype ?pPredicate ?pValue .
    ?genotype gn:speciesName ?speciesName .
    ?genotype gn:inbredSetName ?inbredSetBinomialName .
    ?genotype gn:datasetName ?datasetFullName .
} WHERE {
    ?genotype ?pPredicate ?pValue .
    OPTIONAL {
        ?genotype gn:genotypeOfDataset ?dataset .
        ?dataset gn:fullName ?datasetFullName .
    }.
    OPTIONAL {
        ?genotype gn:genotypeOfDataset ?dataset .
        ?dataset gn:datasetOfInbredSet ?inbredSet .
        ?inbredSet gn:binomialName ?inbredSetBinomialName .
        ?inbredSet gn:inbredSetOfSpecies ?species .
        ?species gn:displayName ?speciesName .
    } .
    FILTER( ?genotype = genotype:$name ) .
    MINUS {
         ?genotype rdf:type ?pValue .
    }
}
"""
    result: MonadicDict = MonadicDict()
    for key, value in sparql_query(
            sparql_conn,
            Template(__metadata_query)
            .substitute(name=name,
                        prefix=RDF_PREFIXES)
    )[0].items():
        result[key] = value
    return result
