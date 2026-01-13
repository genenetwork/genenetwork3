"""RDF

Constants for prefixes and contexts; and wrapper functions around
creating contexts to be used by jsonld when framing and/or compacting.

"""
import json

from SPARQLWrapper import SPARQLWrapper, POST, DIGEST, JSON
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

RDF_PREFIXES = "\n".join(
    [f"PREFIX {key}: <{value}>" for key, value in PREFIXES.items()]
)

BASE_CONTEXT = {
    "data": "@graph",
    "type": "@type",
    "gn": "http://genenetwork.org/id/",
    "gnc": "http://genenetwork.org/category/",
    "gnt": "http://genenetwork.org/term/",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
}

DATASET_CONTEXT = {
    "id": "@id",
    "accessRights": "dct:accessRights",
    "accessionId": "dct:identifier",
    "acknowledgement": "gnt:hasAcknowledgement",
    "altLabel": "skos:altLabel",
    "caseInfo": "gnt:hasCaseInfo",
    "classifiedUnder": "xkos:classifiedUnder",
    "contributors": "dct:creator",
    "contactPoint": "dcat:contactPoint",
    "created": "dct:created",
    "dcat": "http://www.w3.org/ns/dcat#",
    "dct": "http://purl.org/dc/terms/",
    "description": "dct:description",
    "ex": "http://example.org/stuff/1.0/",
    "experimentDesignInfo": "gnt:hasExperimentDesignInfo",
    "experimentType": "gnt:hasExperimentType",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "geoSeriesId": "gnt:hasGeoSeriesId",
    "gnt": "http://genenetwork.org/term/",
    "inbredSet": "gnt:belongsToGroup",
    "label": "rdfs:label",
    "normalization": "gnt:usesNormalization",
    "platformInfo": "gnt:hasPlatformInfo",
    "notes": "gnt:hasNotes",
    "organization": "foaf:Organization",
    "prefLabel": "skos:prefLabel",
    "citation": "dct:isReferencedBy",
    "GoTree": "gnt:hasGOTreeValue",
    "platform": "gnt:usesPlatform",
    "processingInfo": "gnt:hasDataProcessingInfo",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "specifics": "gnt:hasContentInfo",
    "title": "dct:title",
    "xkos": "http://rdf-vocabulary.ddialliance.org/xkos#",
    "tissueInfo": "gnt:hasTissueInfo",
    "tissue": "gnt:hasTissue",
    "contactWebUrl": "foaf:homepage",
    "contactName": "foaf:name",
}

SEARCH_CONTEXT = {
    "pages": "ex:pages",
    "hits": "ex:hits",
    "result": "ex:result",
    "results": "ex:items",
    "resultItem": "ex:resultType",
    "currentPage": "ex:currentPage",
}

DATASET_SEARCH_CONTEXT = SEARCH_CONTEXT | {
    "classifiedUnder": "xkos:classifiedUnder",
    "created": "dct:created",
    "dct": "http://purl.org/dc/terms/",
    "ex": "http://example.org/stuff/1.0/",
    "inbredSet": "ex:belongsToInbredSet",
    "title": "dct:title",
    "name": "rdfs:label",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "type": "@type",
    "xkos": "http://rdf-vocabulary.ddialliance.org/xkos#",
}

PUBLICATION_CONTEXT = {
    "dct": "http://purl.org/dc/terms/",
    "fabio": "http://purl.org/spar/fabio/",
    "prism": "http://prismstandard.org/namespaces/basic/2.0/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "title": "dct:title",
    "journal": "fabio:Journal",
    "volume": "prism:volume",
    "page": "fabio:page",
    "creator": "dct:creator",
    "abstract": "dct:abstract",
    "year": {
        "@id": "fabio:hasPublicationYear",
        "@type": "xsd:gYear",
    },
    "month": {"@id": "prism:publicationDate", "@type": "xsd:gMonth"},
}

PHENOTYPE_CONTEXT = (
    BASE_CONTEXT
    | PUBLICATION_CONTEXT
    | {
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "dcat": "http://www.w3.org/ns/dcat#",
        "prism": "http://prismstandard.org/namespaces/basic/2.0/",
        "traitName": "skos:altLabel",
        "trait": "rdfs:label",
        "altName": "rdfs:altLabel",
        "description": "dct:description",
        "abbreviation": "gnt:abbreviation",
        "labCode": "gnt:labCode",
        "submitter": "gnt:submitter",
        "dataset": "dcat:Distribution",
        "contributor": "dct:contributor",
        "mean": "gnt:mean",
        "locus": "gnt:locus",
        "lodScore": "gnt:lodScore",
        "references": "dct:isReferencedBy",
        "additive": "gnt:additive",
        "sequence": "gnt:sequence",
        "prefLabel": "skos:prefLabel",
        "identifier": "dct:identifier",
        "chromosome": "gnt:chr",
        "mb": "gnt:mb",
        "peakLocation": "gnt:locus",
        "species": "gnt:belongsToSpecies",
        "group": "gnt:belongsToGroup",
    }
)


def sparql_query(query: str, endpoint: str, format_type="json-ld") -> dict:
    """Query virtuoso using a CONSTRUCT query and return a json-ld
    dictionary"""
    sparql = SPARQLWrapper(endpoint)
    if format_type == "json-ld":
        sparql.setQuery(query)
        results = sparql.queryAndConvert()
        return json.loads(results.serialize(format=format_type))  # type: ignore
    # For SELECTs
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    return sparql.queryAndConvert()["results"]["bindings"]  # type: ignore


def query_frame_and_compact(
        query: str, context: dict,
        endpoint: str, options: dict | None = None
) -> dict:
    """Frame and then compact the results given a context"""
    if options is None:
        options = {"graph": True}
    results = sparql_query(query, endpoint)
    return jsonld.compact(
        jsonld.frame(results, context), context, options=options
    )


def query_and_compact(
        query: str, context: dict, endpoint: str, options: dict | None = None
) -> dict:
    """Compact the results given a context"""
    if options is None:
        options = {"graph": True}
    results = sparql_query(query, endpoint)
    return jsonld.compact(results, context, options=options)


def query_and_frame(query: str, context: dict, endpoint: str) -> dict:
    """Frame the results given a context"""
    results = sparql_query(query, endpoint)
    return jsonld.frame(results, context)


def update_rdf(
    query: str, sparql_user: str, sparql_password: str, sparql_auth_uri: str
) -> str:
    """Update RDF Graph content---INSERT/DELETE---in a Graph Store
    using HTTP.  Example return:
    'Insert into <http://genenetwork.org>, 14 (or less) triples -- done'
    """
    sparql = SPARQLWrapper(sparql_auth_uri)
    sparql.setHTTPAuth(DIGEST)
    sparql.setCredentials(sparql_user, sparql_password)
    sparql.setMethod(POST)
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    _r = sparql.queryAndConvert()["results"]  # type: ignore
    return _r["bindings"][0]["callret-0"]["value"]  # type: ignore
