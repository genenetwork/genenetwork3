"""API for fetching metadata using an API"""
import json

from string import Template
from http.client import RemoteDisconnected
from urllib.error import URLError
from flask import Blueprint
from flask import jsonify
from flask import request
from flask import current_app

from pyld import jsonld
from SPARQLWrapper import JSON, JSONLD, SPARQLWrapper

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


@metadata.route("/datasets/search/<term>", methods=["GET"])
def search_datasets(term):
    """Search datasets"""
    try:
        args = request.args
        page = args.get("page", 0)
        page_size = args.get("limit", 10)
        sparql = SPARQLWrapper(current_app.config.get("SPARQL_ENDPOINT"))
        sparql.setQuery(Template("""
$prefix

CONSTRUCT {
        ex:result rdf:type ex:resultType ;
                  ex:totalCount ?totalCount ;
                  ex:currentPage $offset ;
                  ex:items [
                    rdfs:label ?label ;
                    dct:title ?title ;
                    ex:belongsToInbredSet ?inbredSetName ;
                    xkos:classifiedUnder ?datasetType
          ]
} WHERE {
{
        SELECT ?dataset ?label ?inbredSetName ?datasetType ?title WHERE {
        ?dataset rdf:type dcat:Dataset ;
                 rdfs:label ?label ;
                 xkos:classifiedUnder ?inbredSet .
        ?inbredSet ^skos:member gnc:Set ;
                   rdfs:label ?inbredSetName .
        ?label bif:contains "'$term'" .
        OPTIONAL {
          ?dataset dct:title ?title .
        } .
        OPTIONAL {
          ?classification ^xkos:classifiedUnder ?dataset ;
                          ^skos:member gnc:DatasetType ;
                          ?typePredicate ?typeName ;
			  skos:prefLabel ?datasetType .
        }
    } ORDER BY ?dataset LIMIT $limit OFFSET $offset
}

{
        SELECT (COUNT(*)/$limit+1 AS ?totalCount) WHERE {
        ?dataset rdf:type dcat:Dataset ;
                 rdfs:label ?label .
        ?label bif:contains "'$term'" .
        }
}

}
""").substitute(prefix=RDF_PREFIXES, term=term, limit=page_size, offset=page))
        return jsonld.frame(
            json.loads(
                sparql.queryAndConvert().serialize(format="json-ld")),
            {
                "@context": PREFIXES | {
                    "data": "@graph",
                    "type": "@type",
                    "id": "@id",
                    "inbredSet": "ex:belongsToInbredSet",
                    "classifiedUnder": "xkos:classifiedUnder",
                    "dataset": "rdfs:label",
                    "title": "dct:title",
                    "currentPage": "ex:currentPage",
                    "result": "ex:result",
                    "results": "ex:items",
                    "resultItem": "ex:resultType",
                    "pages": "ex:totalCount"
                },
                "type": "resultItem",
            }
        )
    # The virtuoso server is misconfigured or it isn't running at all
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/publications/<name>", methods=["GET"])
def publications(name):
    """Fetch a publication's metadata given it's ACCESSION_ID"""
    try:
        if "unpublished" in name:
            name = f"gn:unpublished{name}"
        else:
            name = f"pubmed:{name}"
        sparql = SPARQLWrapper(current_app.config.get("SPARQL_ENDPOINT"))
        sparql.setQuery(Template("""
$prefix

CONSTRUCT {
    $name ?predicate ?object .
} WHERE {
    $name rdf:type fabio:ResearchPaper ;
          ?predicate ?object .
    FILTER (!regex(str(?predicate), '(hasPubMedId)', 'i')) .
}
""").substitute(name=name, prefix=RDF_PREFIXES))
        return jsonld.compact(
            json.loads(sparql.queryAndConvert().serialize(format="json-ld")),
            {
                "@context": PREFIXES | {
                    "type": "@type",
                    "id": "@id",
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
                    "month": {
                        "@id": "prism:publicationDate",
                        "@type": "xsd:gMonth"
                    },
                },
            })
    # The virtuoso server is misconfigured or it isn't running at all
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/publications/search/<term>", methods=["GET"])
def search_publications(term):
    """Search publications"""
    try:
        args = request.args
        page = args.get("page", 0)
        page_size = args.get("limit", 10)
        sparql = SPARQLWrapper(current_app.config.get("SPARQL_ENDPOINT"))
        sparql.setQuery(Template("""
$prefix

CONSTRUCT {
        ex:result rdf:type ex:resultType ;
                  ex:totalCount ?totalCount ;
                  ex:currentPage $offset ;
                  ex:items [
                     rdfs:label ?publication ;
                     dct:title ?title ;
        ]
} WHERE {
{
        SELECT ?publication ?title ?pmid WHERE {
        ?pub rdf:type fabio:ResearchPaper ;
             ?predicate ?object ;
             dct:title ?title .
        ?object bif:contains "'$term'" .
        BIND( STR(?pub) AS ?publication ) .
        }  ORDER BY ?title LIMIT $limit OFFSET $offset
    }
{
        SELECT (COUNT(*)/$limit+1 AS ?totalCount) WHERE {
        ?publication rdf:type fabio:ResearchPaper ;
                     ?predicate ?object .
        ?object bif:contains "'$term'" .
        }
}
}
""").substitute(prefix=RDF_PREFIXES, term=term, limit=page_size, offset=page))
        results = sparql.queryAndConvert()
        results = json.loads(results.serialize(format="json-ld"))
        frame = {
            "@context": PREFIXES | {
                "data": "@graph",
                "type": "@type",
                "id": "@id",
                "title": "dct:title",
                "pubmed": "fabio:hasPubMedId",
                "currentPage": "ex:currentPage",
                "result": "ex:result",
                "results": "ex:items",
                "resultItem": "ex:resultType",
                "pages": "ex:totalCount",
                "url": "rdfs:label",
            },
            "type": "resultItem",
            "paper": {
                "@type": "fabio:ResearchPaper",
                "@container": "@index"
            }
        }
        return jsonld.frame(results, frame)
    except (RemoteDisconnected, URLError):
        return jsonify({})

@metadata.route("/phenotypes/<name>", methods=["GET"])
def phenotypes(name):
    """Fetch a phenotype's metadata given it's name"""
    try:
        args = request.args
        dataset = args.get("dataset", "")
        sparql = SPARQLWrapper(current_app.config.get("SPARQL_ENDPOINT"))
        sparql.setQuery(Template("""
$prefix

CONSTRUCT {
        ?phenotype ?predicate ?object ;
                   ?pubPredicate ?pubObject ;
                   ex:species ?speciesName ;
                   ex:inbredSet ?inbredSetName ;
                   ex:dataset ?datasetName .
} WHERE {
        ?phenotype skos:altLabel "$name" ;
                   xkos:classifiedUnder ?inbredSet ;
                   ?predicate ?object .
        ?inbredSet ^xkos:classifiedUnder ?phenotype ;
                   rdfs:label ?inbredSetName ;
                   xkos:generalizes ?species .
        ?species skos:prefLabel ?speciesName .
        FILTER (!regex(str(?predicate), '(classifiedUnder)', 'i')) .
        OPTIONAL {
        ?publication ^dct:isReferencedBy ?phenotype ;
                     rdf:type fabio:ResearchPaper ;
                     ?pubPredicate ?pubObject .
        FILTER (!regex(str(?pubPredicate), '(hasPubMedId|type)', 'i')) .
        } .
	OPTIONAL {
	?dataset rdf:type dcat:Dataset ;
                 xkos:classifiedUnder  ?type;
		 rdfs:label "$dataset" ;
		 skos:prefLabel ?datasetName .
	?type ^skos:member gnc:DatasetType .
	FILTER(?type = gnc:Phenotype) .
	}
}
""").substitute(prefix=RDF_PREFIXES, name=name,
                dataset=dataset))
        results = json.loads(sparql.queryAndConvert().serialize(format="json-ld"))
        if not results:
            return jsonify({})
        frame = {
            "@context": PREFIXES | {
                "data": "@graph",
                "type": "@type",
                "id": "@id",
                "traitName": "skos:altLabel",
                "trait": "rdfs:label",
                "altName": "rdfs:altLabel",
                "description": "dct:description",
                "abbreviation": "dct:abbreviation",
                "labCode": "gnt:labCode",
                "submitter": "gnt:submitter",
                "contributor": "dct:contributor",
                "mean": "gnt:mean",
                "locus": "gnt:locus",
                "LRS": "gnt:LRS",
                "references": "dct:isReferencedBy",
                "additive": "gnt:additive",
                "sequence": "gnt:sequence",
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
                "month": {
                    "@id": "prism:publicationDate",
                    "@type": "xsd:gMonth"
                },
            },
            "type": "gnc:Phenotype",
        }
        return jsonld.compact(jsonld.frame(results, frame), frame)
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/genotypes/<name>", methods=["GET"])
def genotypes(name):
    """Fetch a genotype's metadata given it's name"""
    try:
        sparql = SPARQLWrapper(current_app.config.get("SPARQL_ENDPOINT"))
        sparql.setQuery(Template("""
$prefix

CONSTRUCT {
        ?genotype ?predicate ?object .
        ?species rdfs:label ?speciesName .
} WHERE {
        ?genotype rdf:type gnc:Genotype ;
                  rdfs:label "$name" ;
                  ?predicate ?object .
        OPTIONAL {
            ?species ^xkos:classifiedUnder ?genotype ;
                      rdfs:label ?speciesName .
        }
}
""").substitute(prefix=RDF_PREFIXES, name=name))
        results = json.loads(sparql.queryAndConvert().serialize(format="json-ld"))
        if not results:
            return jsonify({})
        frame = {
            "@context": PREFIXES | {
                "data": "@graph",
                "type": "@type",
                "id": "@id",
                "name": "rdfs:label",
                "chr": "gnt:chr",
                "mb": "gnt:mb",
                "mbMm8": "gnt:mbMm8",
                "mb2016": "gnt:mb2016",
                "sequence": "gnt:hasSequence",
                "source": "gnt:hasSource",
                "species": "xkos:classifiedUnder",
                "alternateSource": "gnt:hasAltSourceName",
                "comments": "rdfs:comments",
                "chrNum": {
                    "@id": "gnt:chrNum",
                    "@type": "xsd:int",
                }
            },
            "type": "gnc:Genotype",
        }
        return jsonld.compact(jsonld.frame(results, frame), frame)
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/genewikis/gn/<symbol>", methods=["GET"])
def get_gn_genewiki_entries(symbol):
    """Fetch the GN and NCBI GeneRIF entries"""
    try:
        args = request.args
        page = args.get("page", 0)
        page_size = args.get("limit", 10)
        sparql = SPARQLWrapper(current_app.config.get("SPARQL_ENDPOINT"))
        sparql.setQuery(Template("""
$prefix

CONSTRUCT {
         ?symbol ex:entries [
              rdfs:comment ?comment ;
              ex:species ?species_ ;
              dct:created ?createTime ;
              dct:references ?pmids ;
              dct:creator ?creator ;
              gnt:belongsToCategory ?categories ;
         ] .
         ?symbol rdf:type gnc:GNWikiEntry ;
                 ex:totalCount ?totalCount ;
                 ex:currentPage $offset .
} WHERE {
{
    SELECT ?symbol ?comment (GROUP_CONCAT(DISTINCT ?speciesName; SEPARATOR='; ') AS ?species_)
        ?createTime ?creator
        (GROUP_CONCAT(DISTINCT ?pubmed; SEPARATOR='; ') AS ?pmids)
        (GROUP_CONCAT(DISTINCT ?category; SEPARATOR='; ') AS ?categories)
        WHERE {
        ?symbol rdfs:label ?label ;
                rdfs:comment _:entry .
        ?label bif:contains "'$symbol'" .
        _:entry rdf:type gnc:GNWikiEntry ;
                rdfs:comment ?comment .
        OPTIONAL {
        ?species ^xkos:classifiedUnder _:entry ;
                 ^skos:member gnc:Species ;
                 skos:prefLabel ?speciesName .
        } .
        OPTIONAL { _:entry dct:created ?createTime . } .
        OPTIONAL { _:entry dct:references ?pubmed . } .
        OPTIONAL {
        ?investigator foaf:name ?creator ;
                      ^dct:creator _:entry .
        } .
        OPTIONAL { _:entry gnt:belongsToCategory ?category . } .
    } GROUP BY ?comment ?symbol ?createTime ?creator ORDER BY ?createTime LIMIT $limit OFFSET $offset
}

{
        SELECT (COUNT(DISTINCT ?comment)/$limit+1 AS ?totalCount) WHERE {
        ?symbol rdfs:comment _:entry ;
                rdfs:label ?label .
        _:entry rdfs:comment ?comment ;
                rdf:type gnc:GNWikiEntry .
        ?label bif:contains "'$symbol'" .
        }
}
}
""").substitute(prefix=RDF_PREFIXES, symbol=symbol,
                limit=page_size, offset=page))
        results = sparql.queryAndConvert()
        results = json.loads(results.serialize(format="json-ld"))
        context = {
            "@context": PREFIXES | {
                "data": "@graph",
                "type": "@type",
                "id": "@id",
                "entries": "ex:entries",
                "comment": "rdfs:comment",
                "category": 'gnt:belongsToCategory',
                "author": "dct:creator",
                "pubmed": "dct:references",
                "currentPage": "ex:currentPage",
                "pages": "ex:totalCount",
                "created": {
                    "@id": "dct:created",
                    "@type": "xsd:datetime"
                },
            },
            "type": "gnc:GNWikiEntry"
        }
        return jsonld.compact(
            jsonld.frame(results, context),
            context)
    except (RemoteDisconnected, URLError):
        return jsonify({})
