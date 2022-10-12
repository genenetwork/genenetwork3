"""RDF utilities

This module is a collection of functions that handle SPARQL queries.

"""
import re
from typing import Tuple
from string import Template
from SPARQLWrapper import JSON, SPARQLWrapper
from pymonad.maybe import Just
from gn3.monads import MonadicDict
from gn3.settings import SPARQL_ENDPOINT


def sparql_query(query: str) -> Tuple[MonadicDict, ...]:
    """Run a SPARQL query and return the bound variables."""
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.queryAndConvert()
    if _r := results["results"]["bindings"]:  # type: ignore
        return (*(MonadicDict(bindings) for bindings in _r),)  # type: ignore
    return (MonadicDict(),)


def get_dataset_metadata(accession_id: str) -> MonadicDict:
    """Return info about dataset with ACCESSION_ID."""
    # Check accession_id to protect against query injection.
    # TODO: This function doesn't yet return the names of the actual dataset
    # files.
    pattern = re.compile(r"GN\d+", re.ASCII)
    if not pattern.fullmatch(accession_id):
        return MonadicDict()
    # KLUDGE: We split the SPARQL query because virtuoso is very slow on a
    # single large query.
    queries = [
        """
PREFIX gn: <http://genenetwork.org/>
SELECT ?name ?dataset_group ?status ?title ?geo_series
WHERE {
  ?dataset gn:accessionId "$accession_id" ;
           rdf:type gn:dataset .
  OPTIONAL { ?dataset gn:name ?name } .
  OPTIONAL { ?dataset gn:datasetGroup ?dataset_group } .
  # FIXME: gn:datasetStatus should not be optional. But, some records don't
  # have it.
  OPTIONAL { ?dataset gn:datasetStatus ?status } .
  OPTIONAL { ?dataset gn:title ?title } .
  OPTIONAL { ?dataset gn:geoSeries ?geo_series } .
}
""",
        """
PREFIX gn: <http://genenetwork.org/>
SELECT ?platform_name ?normalization_name ?species_name ?inbred_set_name ?tissue_name
WHERE {
  ?dataset gn:accessionId "$accession_id" ;
           rdf:type gn:dataset ;
           gn:normalization / gn:name ?normalization_name ;
           gn:datasetOfSpecies / gn:menuName ?species_name ;
           gn:datasetOfInbredSet / gn:name ?inbred_set_name .
  OPTIONAL { ?dataset gn:datasetOfTissue / gn:name ?tissue_name } .
  OPTIONAL { ?dataset gn:datasetOfPlatform / gn:name ?platform_name } .
}
""",
        """
PREFIX gn: <http://genenetwork.org/>
SELECT ?specifics ?summary ?about_cases ?about_tissue ?about_platform
       ?about_data_processing ?notes ?experiment_design ?contributors
       ?citation ?acknowledgment
WHERE {
  ?dataset gn:accessionId "$accession_id" ;
           rdf:type gn:dataset .
  OPTIONAL { ?dataset gn:specifics ?specifics . }
  OPTIONAL { ?dataset gn:summary ?summary . }
  OPTIONAL { ?dataset gn:aboutCases ?about_cases . }
  OPTIONAL { ?dataset gn:aboutTissue ?about_tissue . }
  OPTIONAL { ?dataset gn:aboutPlatform ?about_platform . }
  OPTIONAL { ?dataset gn:aboutDataProcessing ?about_data_processing . }
  OPTIONAL { ?dataset gn:notes ?notes . }
  OPTIONAL { ?dataset gn:experimentDesign ?experiment_design . }
  OPTIONAL { ?dataset gn:contributors ?contributors . }
  OPTIONAL { ?dataset gn:citation ?citation . }
  OPTIONAL { ?dataset gn:acknowledgment ?acknowledgment . }
}
""",
    ]
    result: MonadicDict = MonadicDict(
        {
            "accession_id": accession_id,
        }
    )
    query_result: MonadicDict = MonadicDict()
    for query in queries:
        if not (
            # Expecting only one result
            sparql_result := sparql_query(
                Template(query).substitute(accession_id=accession_id)
            )[0]
        ):
            return MonadicDict()
        query_result |= sparql_result
    for key, value in query_result.items():
        result[key] = value.bind(lambda x: Just(x["value"]))

    investigator_query_result = sparql_query(
        Template(
            """
PREFIX gn: <http://genenetwork.org/>
SELECT ?name ?address ?city ?state ?zip ?phone ?email ?country ?homepage
WHERE {
  ?dataset gn:accessionId "$accession_id" ;
           rdf:type gn:dataset ;
           gn:datasetOfInvestigator ?investigator .
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
    """
        ).substitute(accession_id=accession_id)
    )[0]
    result["investigators"] = Just({
        key: value.bind(lambda a: a["value"])
                for key, value in investigator_query_result.items()
    })
    return result
