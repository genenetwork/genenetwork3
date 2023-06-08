"""API for fetching metadata using an API"""
from string import Template
from http.client import RemoteDisconnected
from urllib.error import URLError
from flask import Blueprint
from flask import jsonify
from flask import current_app

from SPARQLWrapper import SPARQLWrapper

from gn3.db.rdf import get_dataset_metadata
from gn3.db.rdf import get_publication_metadata
from gn3.db.rdf import get_phenotype_metadata
from gn3.db.rdf import sparql_query
from gn3.db.rdf import RDF_PREFIXES


metadata = Blueprint("metadata", __name__)


@metadata.route("/dataset/<name>", methods=["GET"])
def dataset(name):
    """Fetch a dataset's metadata given it's ACCESSION_ID"""
    try:
        return jsonify(
            get_dataset_metadata(
                SPARQLWrapper(current_app.config.get("SPARQL_ENDPOINT")),
                name,
            ).data
        )
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
