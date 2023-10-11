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
    "foaf": "http://xmlns.com/foaf/0.1/",
    "generif": "http://www.ncbi.nlm.nih.gov/gene?cmd=Retrieve&dopt=Graphics&list_uids=",
    "genotype": "http://genenetwork.org/genotype/",
    "gn": "http://genenetwork.org/id/",
    "gnc": "http://genenetwork.org/category/",
    "gnt": "http://genenetwork.org/term/",
    "owl": "http://www.w3.org/2002/07/owl#",
    "phenotype": "http://genenetwork.org/phenotype/",
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


def get_dataset_metadata(
        sparql_conn: SPARQLWrapper, name: str
) -> MonadicDict:
    """Return info about dataset with a given NAME"""
    response: MonadicDict = MonadicDict()
    for key, value in sparql_query(
            sparql_conn,
            Template("""
$prefix

CONSTRUCT {
	  ?dataset ?predicate ?term .
	  ?dataset gnt:classifiedUnder ?inbredSetName .
          ?dataset gnt:usesNormalization ?normalizationLabel .
          ?typePredicate ex:DatasetType ?typeName .
} WHERE {
	 ?dataset rdf:type dcat:Dataset .
	 ?dataset ?predicate ?term .
	 ?dataset xkos:classifiedUnder ?inbredSet .
	 gnc:Set skos:member ?inbredSet .
	 ?dataset (rdfs:label|dct:identifier) "$name" .
	 ?inbredSet rdfs:label ?inbredSetName .
         OPTIONAL {
            ?dataset xkos:classifiedUnder ?type .
            gnc:DatasetType skos:member ?type .
            ?type ?typePredicate ?typeName .
            ?type (skos:altLabel|skos:prefLabel) ?typeName .
         } .
         OPTIONAL {
            ?dataset gnt:usesNormalization ?normalization .
            ?normalization rdfs:label ?normalizationLabel .
         }
	 FILTER (!regex(str(?predicate), '(classifiedUnder|usesNormalization)','i')) .
}""")
            .substitute(
                prefix=RDF_PREFIXES,
                name=name
            )
    )[0].items():
        response[key] = value
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
