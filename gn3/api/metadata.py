"""API for fetching metadata using an API"""
import json

from string import Template
from http.client import RemoteDisconnected
from urllib.error import URLError
from flask import Blueprint
from flask import jsonify
from flask import current_app

from pyld import jsonld
from SPARQLWrapper import JSON, JSONLD, SPARQLWrapper

from gn3.db.rdf import get_dataset_metadata
from gn3.db.rdf import get_publication_metadata
from gn3.db.rdf import get_phenotype_metadata
from gn3.db.rdf import get_genotype_metadata
from gn3.db.rdf import sparql_query
from gn3.db.rdf import RDF_PREFIXES, PREFIXES


metadata = Blueprint("metadata", __name__)


@metadata.route("/datasets/<name>", methods=["GET"])
def datasets(name):
    """Fetch a dataset's metadata given it's ACCESSION_ID or NAME"""
    try:
        sparql = SPARQLWrapper(current_app.config.get("SPARQL_ENDPOINT"))
        sparql.setQuery(Template("""
$prefix

CONSTRUCT {
	  ?dataset ?predicate ?term ;
                   rdf:type dcat:Dataset ;
	           ex:belongsToInbredSet ?inbredSetName ;
                   gnt:usesNormalization ?normalizationLabel ;
                   dcat:contactPoint ?investigatorName ;
                   xkos:classifiedUnder  ?altName ;
                   ex:platform ?platform ;
                   ex:tissue ?tissue .
          ?platform ?platformPred  ?platformObject ;
                    ex:info ?platformInfo .
          ?tissue rdfs:label ?tissueName ;
                  rdf:type gnc:tissue ;
                  ex:info ?tissueInfo .
} WHERE {
	 ?dataset rdf:type dcat:Dataset ;
	          xkos:classifiedUnder ?inbredSet ;
                  rdfs:label "$name" .
         OPTIONAL {
            ?inbredSet ^skos:member gnc:Set ;
                       rdfs:label ?inbredSetName .
         } .
         OPTIONAL {
            ?type ^xkos:classifiedUnder ?dataset ;
                  ^skos:member gnc:DatasetType ;
                  skos:prefLabel ?altName .
         } .
         OPTIONAL {
            ?normalization ^gnt:usesNormalization ?dataset ;
                           rdfs:label ?normalizationLabel .
         } .
         OPTIONAL {
           ?investigator foaf:name ?investigatorName ;
                         ^dcat:contactPoint ?dataset .
         } .
         OPTIONAL {
           ?platform ^gnt:usesPlatform ?dataset ;
                     ?platformPred  ?platformObject .
         } .
         OPTIONAL {
           ?dataset gnt:hasPlatformInfo ?platformInfo .
         } .
         OPTIONAL {
           ?dataset gnt:hasTissueInfo ?tissueInfo .
         } .
         OPTIONAL {
           ?dataset gnt:hasTissue ?tissue .
           ?tissue rdfs:label ?tissueName .
         } .
	 FILTER (!regex(str(?predicate), '(classifiedUnder|usesNormalization|contactPoint|hasPlatformInfo|tissueInfo)', 'i')) .
         FILTER (!regex(str(?platformPred), '(classifiedUnder|geoSeriesId|hasGoTreeValue)', 'i')) .
}""").substitute(prefix=RDF_PREFIXES, name=name))
        results = sparql.queryAndConvert()
        results = json.loads(
            results.serialize(format="json-ld")
        )
        frame = {
            "@context": PREFIXES | {
                "data": "@graph",
                "type": "@type",
                "id": "@id",
                "inbredSet": "ex:belongsToInbredSet",
                "description": "dct:description",
                "created":  "dct:created",
                "normalization": "gnt:usesNormalization",
                "classifiedUnder": "xkos:classifiedUnder",
                "accessRights": "dct:accessRights",
                "accessionId": "dct:identifier",
                "title": "dct:title",
                "label": "rdfs:label",
                "altLabel": "skos:altLabel",
                "prefLabel": "skos:prefLabel",
                "contactPoint": "dcat:contactPoint",
                "organization": "foaf:Organization",
                "info": "ex:info",
                "caseInfo": "gnt:hasCaseInfo",
                "geoSeriesId": "gnt:hasGeoSeriesId",
                "experimentDesignInfo": "gnt:hasExperimentDesignInfo",
                "notes": "gnt:hasNotes",
                "processingInfo": "gnt:hasDataProcessingInfo",
                "acknowledgement": "gnt:hasAcknowledgement",
                "tissue": "ex:tissue",
                "platform": "ex:platform",
            },
            "type": "dcat:Dataset",
        }
        return jsonld.compact(jsonld.frame(results, frame), frame)
    # The virtuoso server is misconfigured or it isn't running at all
    except (RemoteDisconnected, URLError):
        return jsonify({})
    # The virtuoso server is misconfigured or it isn't running at all
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/publication/<name>", methods=["GET"])
def publication(name):
    """Fetch a publication's metadata given it's ACCESSION_ID"""
    try:
        if "unpublished" in name:
            name = f"gn:{name}"
        else:
            name = f"publication:{name}"
        return jsonify(
            get_publication_metadata(
                SPARQLWrapper(current_app.config.get("SPARQL_ENDPOINT")),
                name,
            ).data
        )
    # The virtuoso server is misconfigured or it isn't running at all
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/phenotype/<name>", methods=["GET"])
def phenotype(name):
    """Fetch a phenotype's metadata given it's name"""
    try:
        return jsonify(
            get_phenotype_metadata(
                SPARQLWrapper(current_app.config.get("SPARQL_ENDPOINT")),
                name,
            ).data
        )
    # The virtuoso server is misconfigured or it isn't running at all
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/genotype/<name>", methods=["GET"])
def genotype(name):
    """Fetch a genotype's metadata given it's name"""
    try:
        return jsonify(
            get_genotype_metadata(
                SPARQLWrapper(current_app.config.get("SPARQL_ENDPOINT")),
                name,
            ).data
        )
    # The virtuoso server is misconfigured or it isn't running at all
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/genewiki/<symbol>", methods=["GET"])
def get_genewiki_entries(symbol):
    """Fetch the GN and NCBI GeneRIF entries"""
    try:
        gn_entries = sparql_query(
            sparql_conn=SPARQLWrapper(current_app.config.get("SPARQL_ENDPOINT")),
            query=Template("""
$rdf_prefixes

SELECT ?author ?geneCategory (STR(?gnEntry) AS ?entry)
       (STR(?createdOn) AS ?created)
       (GROUP_CONCAT(DISTINCT ?pmid; SEPARATOR=',') AS ?PubMedId)
       ?weburl
WHERE {
  ?generif gn:symbol ?symbol .
  ?generif gn:geneWikiEntryOfGn _:gnEntry .
  _:gnEntry gn:geneWikiEntry ?gnEntry;
            dct:creator ?author;
            dct:created ?createdOn .
  OPTIONAL { _:gnEntry gn:geneCategory ?geneCategory } .
  OPTIONAL { _:gnEntry foaf:homepage ?weburl } .
  OPTIONAL { _:gnEntry dct:source ?pmid} .
  OPTIONAL {
    ?generif gn:wikiEntryOfSpecies ?speciesName .
    ?species gn:name ?speciesName ;
             gn:binomialName ?speciesBinomialName .
  } .
  FILTER( lcase(?symbol) = '$symbol' )
} GROUP BY ?author ?createdOn ?gnEntry
           ?generif ?symbol ?weburl
	   ?geneCategory
ORDER BY ASC(?createdOn)""").substitute(rdf_prefixes=RDF_PREFIXES,
                                        symbol=str(symbol).lower()))
        ncbi_entries = sparql_query(
            sparql_conn=SPARQLWrapper(current_app.config.get("SPARQL_ENDPOINT")),
            query=Template("""
$rdf_prefixes

SELECT ?speciesBinomialName (STR(?gnEntry) AS ?entry)
       (STR(?createdOn) AS ?createdOn)
       (GROUP_CONCAT(DISTINCT REPLACE(STR(?pmid), pubmed:, ''); SEPARATOR=',') AS ?PubMedId)
       ?generif
WHERE {
  ?generif gn:symbol ?symbol .
  ?generif gn:geneWikiEntryOfNCBI [
    gn:geneWikiEntry ?gnEntry ;
    dct:created ?createdOn ;
    dct:source ?pmid
  ] .
  OPTIONAL {
    ?generif gn:wikiEntryOfSpecies ?speciesName .
    ?species gn:name ?speciesName ;
             gn:binomialName ?speciesBinomialName .
  } .
  FILTER( lcase(?symbol) = '$symbol' )
} GROUP BY ?createdOn ?gnEntry
           ?generif ?symbol
	   ?speciesBinomialName
ORDER BY ASC(?createdOn)""").substitute(rdf_prefixes=RDF_PREFIXES,
                                        symbol=str(symbol).lower()))
        return jsonify({
            "gn_entries": list(map(lambda x: x.data, gn_entries)),
            "ncbi_entries": list(map(lambda x: x.data, ncbi_entries)),
        })
    except (RemoteDisconnected, URLError):
        return jsonify({
            "gn_entries": {},
            "ncbi_entries": {},
        })
