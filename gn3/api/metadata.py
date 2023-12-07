"""API for fetching metadata using an API"""
from string import Template
from http.client import RemoteDisconnected
from urllib.error import URLError
from flask import Blueprint
from flask import jsonify
from flask import request
from flask import current_app

from gn3.db.rdf import RDF_PREFIXES
from gn3.db.rdf import (query_frame_and_compact,
                        query_and_compact,
                        query_and_frame)


BASE_CONTEXT = {
    "data": "@graph",
    "id": "@id",
    "type": "@type",
}

DATASET_CONTEXT = {
    "accessRights": "dct:accessRights",
    "accessionId": "dct:identifier",
    "acknowledgement": "gnt:hasAcknowledgement",
    "altLabel": "skos:altLabel",
    "caseInfo": "gnt:hasCaseInfo",
    "classifiedUnder": "xkos:classifiedUnder",
    "contributors": "dct:creator",
    "contactPoint": "dcat:contactPoint",
    "created":  "dct:created",
    "dcat": "http://www.w3.org/ns/dcat#",
    "dct": "http://purl.org/dc/terms/",
    "description": "dct:description",
    "ex": "http://example.org/stuff/1.0/",
    "experimentDesignInfo": "gnt:hasExperimentDesignInfo",
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
    "GoTree": "gnt:hasGoTreeValue",
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
    "created":  "dct:created",
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
    "month": {
        "@id": "prism:publicationDate",
        "@type": "xsd:gMonth"
    },
}

PHENOTYPE_CONTEXT = BASE_CONTEXT | PUBLICATION_CONTEXT | {
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "gnt": "http://genenetwork.org/term/",
    "dcat": "http://www.w3.org/ns/dcat#",
    "prism": "http://prismstandard.org/namespaces/basic/2.0/",
    "gnc": "http://genenetwork.org/category/",
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

metadata = Blueprint("metadata", __name__)


@metadata.route("/datasets/<name>", methods=["GET"])
def datasets(name):
    """Fetch a dataset's metadata given it's ACCESSION_ID or NAME"""
    try:
        _query = Template("""
$prefix

CONSTRUCT {
	  ?dataset ?predicate ?term .
          ?inbredSet rdfs:label ?inbredSetName .
          ?platform ?platformPred  ?platformObject ;
                    gnt:hasPlatformInfo ?platformInfo .
          ?normalization ?normalizationPred ?normalizationObj .
          ?tissue ?tissuePred ?tissueObj ;
                  gnt:hasTissueInfo ?tissueInfo .
          ?investigator foaf:name ?investigatorName ;
                       foaf:homepage ?homepage .
          ?type skos:prefLabel ?altName .
} WHERE {
	 ?dataset rdf:type dcat:Dataset ;
                  ?predicate ?term ;
                  (rdfs:label|dct:identifier|skos:prefLabel) "$name" .
        FILTER (!regex(str(?predicate), '(hasTissueInfo)', 'i')) .
        FILTER (!regex(str(?predicate), '(usesNormalization)', 'i')) .
        FILTER (!regex(str(?predicate), '(platformInfo)', 'i')) .
         OPTIONAL {
            ?inbredSet ^skos:member gnc:Set ;
                       ^gnt:belongsToGroup ?dataset ;
                        rdfs:label ?inbredSetName .
         } .
         OPTIONAL {
            ?type ^xkos:classifiedUnder ?dataset ;
                  ^skos:member gnc:DatasetType ;
                  skos:prefLabel ?altName .
         } .
         OPTIONAL {
           ?investigator foaf:name ?investigatorName ;
                         foaf:homepage ?homepage ;
                         ^dcat:contactPoint ?dataset .
         } .
         OPTIONAL {
           ?platform ^gnt:usesPlatform ?dataset ;
                     ?platformPred  ?platformObject .
         } .
         OPTIONAL {
           ?normalization ^gnt:usesNormalization ?dataset ;
                          ?normalizationPred ?normalizationObj .
         }
         OPTIONAL { ?dataset gnt:hasPlatformInfo ?platformInfo . } .
         OPTIONAL { ?dataset gnt:hasTissueInfo ?tissueInfo . } .
         OPTIONAL {
           ?dataset gnt:hasTissue ?tissue .
           ?tissue rdfs:label ?tissueName ;
                   ?tissuePred ?tissueObj .
         } .
}""").substitute(prefix=RDF_PREFIXES, name=name)
        _context = {
            "@context": BASE_CONTEXT | DATASET_CONTEXT,
            "type": "dcat:Dataset",
        }
        return query_frame_and_compact(
            _query, _context,
            current_app.config.get("SPARQL_ENDPOINT")
        )
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/datasets/<group>/list", methods=["GET"])
def list_datasets_by_group(group):
    """List datasets that belong to a given group"""
    try:
        args = request.args
        page = args.get("page", 0)
        page_size = args.get("per-page", 10)
        _query = Template("""
$prefix

CONSTRUCT {
         ex:result rdf:type ex:resultType ;
                  ex:totalCount ?totalCount ;
                  ex:currentPage $offset ;
                  ex:items [
                     rdfs:label ?datasetName ;
                     dct:identifier ?accessionId ;
                     dct:created ?createTime ;
                     dct:title ?title ;
         ] .
} WHERE {
{
         SELECT ?datasetName ?accessionId ?createTime ?title WHERE {
	 ?dataset rdf:type dcat:Dataset ;
                  rdfs:label ?datasetName .
         ?inbredSet ^skos:member gnc:Set ;
                    ^xkos:classifiedUnder ?dataset ;
                    rdfs:label ?inbredSetName ;
                    skos:prefLabel ?group .
         ?group bif:contains "$group" .
         OPTIONAL { ?dataset dct:identifier ?accesionId . } .
         OPTIONAL { ?dataset dct:created ?createTime . } .
         OPTIONAL { ?dataset dct:title ?title . } .
        } ORDER BY ?createTime LIMIT $limit OFFSET $offset
}
{
        SELECT (COUNT(DISTINCT ?dataset)/$limit+1 AS ?totalCount) WHERE {
        ?dataset rdf:type dcat:Dataset ;
                 rdfs:label ?datasetName .
        ?inbredSet ^skos:member gnc:Set ;
                   ^xkos:classifiedUnder ?dataset ;
                   rdfs:label ?inbredSetName ;
                   skos:prefLabel ?group .
        ?group bif:contains "$group" .
        }
}
}
""").substitute(prefix=RDF_PREFIXES, group=group, limit=page_size, offset=page)
        _context = {
            "@context": BASE_CONTEXT | DATASET_SEARCH_CONTEXT,
            "type": "resultItem",
        }
        return query_frame_and_compact(
            _query, _context,
            current_app.config.get("SPARQL_ENDPOINT")
        )
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/datasets/search/<term>", methods=["GET"])
def search_datasets(term):
    """Search datasets"""
    try:
        args = request.args
        page = args.get("page", 0)
        page_size = args.get("per-page", 10)
        _query = Template("""
$prefix

CONSTRUCT {
        ex:result rdf:type ex:resultType ;
                  ex:pages ?pages ;
                  ex:hits ?hits ;
                  ex:currentPage $offset ;
                  ex:items [
                    rdfs:label ?label ;
                    dct:title ?title ;
                    ex:belongsToInbredSet ?inbredSetName ;
                    xkos:classifiedUnder ?datasetType ;
          ]
} WHERE {
{
        SELECT DISTINCT ?dataset ?label ?inbredSetName ?datasetType ?title WHERE {
        ?dataset rdf:type dcat:Dataset ;
                 rdfs:label ?label ;
                 ?datasetPredicate ?datasetObject ;
                 xkos:classifiedUnder ?inbredSet .
        ?inbredSet ^skos:member gnc:Set ;
                   rdfs:label ?inbredSetName .
        ?datasetObject bif:contains "'$term'" .
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
        SELECT (COUNT(DISTINCT ?dataset)/$limit+1 AS ?pages) (COUNT(DISTINCT ?dataset) AS ?hits) WHERE {
        ?dataset rdf:type dcat:Dataset ;
                 ?p ?o .
        ?o bif:contains "'$term'" .
        }
}

}
""").substitute(prefix=RDF_PREFIXES, term=term, limit=page_size, offset=page)
        _context = {
                "@context": BASE_CONTEXT | DATASET_SEARCH_CONTEXT,
                "type": "resultItem",
        }
        return query_frame_and_compact(
            _query, _context,
            current_app.config.get("SPARQL_ENDPOINT")
        )
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/publications/<name>", methods=["GET"])
def publications(name):
    """Fetch a publication's metadata given it's NAME"""
    try:
        if "unpublished" in name:
            name = f"gn:unpublished{name}"
        else:
            name = f"pubmed:{name}"
        _query = Template("""
$prefix

CONSTRUCT {
    $name ?predicate ?object .
} WHERE {
    $name rdf:type fabio:ResearchPaper ;
          ?predicate ?object .
    FILTER (!regex(str(?predicate), '(hasPubMedId)', 'i')) .
}
""").substitute(name=name, prefix=RDF_PREFIXES)
        return query_and_compact(
            _query, {"@context": BASE_CONTEXT | PUBLICATION_CONTEXT},
            current_app.config.get("SPARQL_ENDPOINT")
        )
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/publications/search/<term>", methods=["GET"])
def search_publications(term):
    """Search publications"""
    try:
        args = request.args
        page = args.get("page", 0)
        page_size = args.get("per-page", 10)
        _query = Template("""
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
""").substitute(prefix=RDF_PREFIXES, term=term, limit=page_size, offset=page)
        _context = {
            "@context": BASE_CONTEXT | SEARCH_CONTEXT | {
                "dct": "http://purl.org/dc/terms/",
                "ex": "http://example.org/stuff/1.0/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "fabio": "http://purl.org/spar/fabio/",
                "title": "dct:title",
                "pubmed": "fabio:hasPubMedId",
                "currentPage": "ex:currentPage",
                "url": "rdfs:label",
            },
            "type": "resultItem",
            "paper": {
                "@type": "fabio:ResearchPaper",
                "@container": "@index"
            }
        }
        return query_and_frame(
            _query, _context,
            current_app.config.get("SPARQL_ENDPOINT")
        )
    except (RemoteDisconnected, URLError):
        return jsonify({})

@metadata.route("/phenotypes/<name>",methods=["GET"])
@metadata.route("/phenotypes/<group>/<name>", methods=["GET"])
def phenotypes(name, group=None):
    """Fetch a phenotype's metadata given it's name"""
    try:
        if group:
            name = f"{group}_{name}"
        _query = Template("""
$prefix

CONSTRUCT {
        ?phenotype ?predicate ?object ;
                   gnt:belongsToSpecies ?speciesName ;
                   dcat:Distribution ?dataset ;
                   gnt:belongsToGroup ?inbredSetName ;
                   gnt:locus ?geno .
        ?dataset skos:prefLabel ?datasetName ;
                 dct:identifier ?datasetLabel ;
                 rdf:type dcat:Dataset .
        ?publication ?pubPredicate ?pubObject .
        ?geno rdfs:label ?locus ;
              gnt:chr ?chr ;
              gnt:mb ?mb .
} WHERE {
        ?phenotype skos:altLabel "$name" ;
                   gnt:belongsToGroup ?inbredSet ;
                   ?predicate ?object .
        ?inbredSet rdfs:label ?inbredSetName ;
                   xkos:generalizes ?species .
        ?species skos:prefLabel ?speciesName .
        OPTIONAL {
        ?publication ^dct:isReferencedBy ?phenotype ;
                     rdf:type fabio:ResearchPaper ;
                     ?pubPredicate ?pubObject .
        FILTER (!regex(str(?pubPredicate), '(hasPubMedId|type)', 'i')) .
        } .
        OPTIONAL {
        ?geno ^gnt:locus ?phenotype ;
              rdf:type gnc:Genotype ;
              rdfs:label ?locus ;
              gnt:chr ?chr ;
              gnt:mb ?mb .
        } .
	OPTIONAL {
	?dataset rdf:type dcat:Dataset ;
                 gnt:belongsToGroup ?inbredSet ;
                 xkos:classifiedUnder gnc:Phenotype ;
                 rdfs:label ?datasetLabel ;
		 skos:prefLabel ?datasetName .
	?type ^skos:member gnc:DatasetType .
	FILTER(?type = gnc:Phenotype) .
	}
}
""").substitute(prefix=RDF_PREFIXES, name=name)
        _context = {
            "@context": PHENOTYPE_CONTEXT,
            "dataset": {
                "type": "dcat:Dataset",
            },
            "type": "gnc:Phenotype",
        }
        return query_frame_and_compact(
            _query, _context,
            current_app.config.get("SPARQL_ENDPOINT")
        )
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/genotypes/<name>", methods=["GET"])
def genotypes(name):
    """Fetch a genotype's metadata given it's name"""
    try:
        _query = Template("""
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
""").substitute(prefix=RDF_PREFIXES, name=name)
        _context = {
            "@context": BASE_CONTEXT | {
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "gnt": "http://genenetwork.org/term/",
                "xkos": "http://rdf-vocabulary.ddialliance.org/xkos#",
                "gnc": "http://genenetwork.org/category/",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
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
        return query_frame_and_compact(
            _query, _context,
            current_app.config.get("SPARQL_ENDPOINT")
        )
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/genewikis/gn/<symbol>", methods=["GET"])
def get_gn_genewiki_entries(symbol):
    """Fetch the GN and NCBI GeneRIF entries"""
    try:
        args = request.args
        page = args.get("page", 0)
        page_size = args.get("per-page", 10)
        _query = Template("""
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
                limit=page_size, offset=page)
        _context = {
            "@context": BASE_CONTEXT | {
                "ex": "http://example.org/stuff/1.0/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "gnt": "http://genenetwork.org/term/",
                "gnc": "http://genenetwork.org/category/",
                "dct": "http://purl.org/dc/terms/",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                "entries": "ex:entries",
                "comment": "rdfs:comment",
                "species": "ex:species",
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
        return query_frame_and_compact(
            _query, _context,
            current_app.config.get("SPARQL_ENDPOINT")
        )
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/genewikis/ncbi/<symbol>", methods=["GET"])
def get_ncbi_genewiki_entries(symbol):
    """Fetch the NCBI GeneRIF entries"""
    try:
        args = request.args
        page, page_size = args.get("page", 0), args.get("per-page", 10)
        _query = Template("""
$prefix

CONSTRUCT {
         ?symbol ex:entries [
              rdfs:comment ?comment ;
              gnt:hasGeneId ?geneId ;
              ex:species ?species_ ;
              dct:created ?createTime ;
              dct:references ?pmids ;
              dct:creator ?creator ;
         ] .
         ?symbol rdf:type gnc:GNWikiEntry ;
                 ex:totalCount ?totalCount ;
                 ex:currentPage $offset .
} WHERE {
{
    SELECT ?symbol ?comment ?geneId (GROUP_CONCAT(DISTINCT ?speciesName; SEPARATOR='; ') AS ?species_)
        ?createTime ?creator
        (GROUP_CONCAT(DISTINCT ?pubmed; SEPARATOR='; ') AS ?pmids)
        WHERE {
        ?symbol rdfs:label ?label ;
                rdfs:comment _:entry .
        ?label bif:contains "'$symbol'" .
        _:entry rdf:type gnc:NCBIWikiEntry ;
                rdfs:comment ?comment .
        OPTIONAL {
        ?species ^xkos:classifiedUnder _:entry ;
                 ^skos:member gnc:Species ;
                 skos:prefLabel ?speciesName .
        } .
        OPTIONAL { _:entry gnt:hasGeneId ?geneId . } .
        OPTIONAL { _:entry dct:created ?createTime . } .
        OPTIONAL { _:entry dct:references ?pubmed . } .
        OPTIONAL {
        ?investigator foaf:name ?creator ;
                      ^dct:creator _:entry .
        } .
    } GROUP BY ?comment ?symbol ?createTime ?creator ?geneId ORDER BY ?createTime LIMIT $limit OFFSET $offset
}

{
        SELECT (COUNT(DISTINCT ?comment)/$limit+1 AS ?totalCount) WHERE {
        ?symbol rdfs:comment _:entry ;
                rdfs:label ?label .
        _:entry rdfs:comment ?comment ;
                rdf:type gnc:NCBIWikiEntry .
        ?label bif:contains "'$symbol'" .
        }
}
}
""").substitute(prefix=RDF_PREFIXES, symbol=symbol,
                limit=page_size, offset=page)
        _context = {
            "@context": BASE_CONTEXT | {
                "ex": "http://example.org/stuff/1.0/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "gnt": "http://genenetwork.org/term/",
                "gnc": "http://genenetwork.org/category/",
                "dct": "http://purl.org/dc/terms/",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                "entries": "ex:entries",
                "comment": "rdfs:comment",
                "category": 'gnt:belongsToCategory',
                "author": "dct:creator",
                "species": "ex:species",
                "geneId": "gnt:hasGeneId",
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
        return query_frame_and_compact(
            _query, _context,
            current_app.config.get("SPARQL_ENDPOINT")
        )
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/species", methods=["GET"])
def list_species():
    """List all species"""
    try:
        _query = Template("""
$prefix

CONSTRUCT {
        ?species ?predicate ?object .
} WHERE {
        ?species ^skos:member gnc:Species ;
                 ?predicate ?object .
        VALUES ?predicate {
               rdfs:label skos:prefLabel
               skos:altLabel gnt:shortName
               gnt:family skos:notation
        }

}
""").substitute(prefix=RDF_PREFIXES)
        _context = {
            "@context": BASE_CONTEXT | {
                "skos": "http://www.w3.org/2004/02/skos/core#",
                "gnt": "http://genenetwork.org/term/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "name": "rdfs:label",
                "family": "gnt:family",
                "shortName": "gnt:shortName",
                "alternateName": "skos:altLabel",
                "taxonomicId": "skos:notation",
                "fullName": "skos:prefLabel",
            },
        }
        return query_and_compact(
            _query, _context,
            current_app.config.get("SPARQL_ENDPOINT")
        )
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/species/<name>", methods=["GET"])
def fetch_species(name):
    """Fetch a Single species information"""
    try:
        _query = Template("""
$prefix

CONSTRUCT {
        ?species ?predicate ?object .
} WHERE {
        ?species ^skos:member gnc:Species ;
                 gnt:shortName "$name" ;
                 ?predicate ?object .
        VALUES ?predicate {
               rdfs:label skos:prefLabel
               skos:altLabel gnt:shortName
               gnt:family skos:notation
        }

}
""").substitute(prefix=RDF_PREFIXES, name=name)
        _context = {
            "@context": BASE_CONTEXT | {
                "skos": "http://www.w3.org/2004/02/skos/core#",
                "gnt": "http://genenetwork.org/term/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "name": "rdfs:label",
                "family": "gnt:family",
                "shortName": "gnt:shortName",
                "alternateName": "skos:altLabel",
                "taxonomicId": "skos:notation",
                "fullName": "skos:prefLabel",
            },
        }
        return query_and_compact(
            _query, _context,
            current_app.config.get("SPARQL_ENDPOINT")
        )
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/groups", methods=["GET"])
def groups():
    """Fetch the list of groups"""
    try:
        _query = Template("""
$prefix

CONSTRUCT {
        ?group ?predicate ?object .
} WHERE {
        ?group ^skos:member gnc:Set ;
                 ?predicate ?object .
        VALUES ?predicate {
               rdfs:label skos:prefLabel
               gnt:geneticType gnt:mappingMethod
               gnt:code gnt:family
        }

}
""").substitute(prefix=RDF_PREFIXES)
        _context = {
            "@context": BASE_CONTEXT | {
                "skos": "http://www.w3.org/2004/02/skos/core#",
                "gnt": "http://genenetwork.org/term/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "name": "rdfs:label",
                "family": "gnt:family",
                "shortName": "gnt:shortName",
                "code": "gnt:code",
                "mappingMethod": "gnt:mappingMethod",
                "geneticType": "gnt:geneticType",
                "fullName": "skos:prefLabel",
            },
        }
        return query_and_compact(
            _query, _context,
            current_app.config.get("SPARQL_ENDPOINT")
        )
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/groups/<name>", methods=["GET"])
def fetch_group_by_species(name):
    """Fetch the list of groups (I.e. Inbredsets)"""
    try:
        _query = Template("""
$prefix

CONSTRUCT {
        ?group ?predicate ?object .
} WHERE {
        ?species gnt:shortName "$name" ;
                 ^skos:member gnc:Species .
        ?group ^skos:member gnc:Set ;
               xkos:generalizes ?species ;
               ?predicate ?object .
        VALUES ?predicate {
               rdfs:label skos:prefLabel
               gnt:geneticType gnt:mappingMethod
               gnt:code gnt:family
        }

}
""").substitute(prefix=RDF_PREFIXES, name=name)
        _context = {
            "@context": BASE_CONTEXT | {
                "skos": "http://www.w3.org/2004/02/skos/core#",
                "gnt": "http://genenetwork.org/term/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "name": "rdfs:label",
                "family": "gnt:family",
                "shortName": "gnt:shortName",
                "code": "gnt:code",
                "mappingMethod": "gnt:mappingMethod",
                "geneticType": "gnt:geneticType",
                "fullName": "skos:prefLabel",
            },
        }
        return query_and_compact(
            _query, _context,
            current_app.config.get("SPARQL_ENDPOINT")
        )
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/probesets/<name>", methods=["GET"])
def probesets(name):
    """Fetch a probeset's metadata given it's name"""
    try:
        _query = Template("""
$prefix

CONSTRUCT {
        ?probeset ?predicate ?object ;
                  gnt:hasChip ?chipName .
} WHERE {
        ?probeset rdf:type gnc:Probeset ;
                  rdfs:label "$name" ;
                  ?predicate ?object .
        FILTER (?predicate != gnt:hasChip) .
        OPTIONAL{
            ?probeset gnt:hasChip ?chip .
            ?chip rdfs:label ?chipName .
        } .
}
""").substitute(prefix=RDF_PREFIXES, name=name)
        _context = {
            "@context": BASE_CONTEXT | {
                "gnt": "http://genenetwork.org/term/",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "skos": "http://www.w3.org/2004/02/skos/core#",
                "dct": "http://purl.org/dc/terms/",
                "name": "rdfs:label",
                "alias": "skos:altLabel",
                "chip": "gnt:hasChip",
                "targetId": "gnt:hasTargetId",
                "symbol": "gnt:symbol",
                "description": "dct:description",
                "targetsRegion": "gnt:targetsRegion",
                "chr": "gnt:chr",
                "mb": "gnt:mb",
                "mbMm8": "gnt:mbMm8",
                "mb2016": "gnt:mb2016",
                "specificity": "gnt:hasSpecificity",
                "blatScore": "gnt:hasBlatScore",
                "blatMbStart": "gnt:hasBlatMbStart",
                "blatMbStart2016": "gnt:hasBlatMbStart2016",
                "blatMbEnd": "gnt:hasBlatMbEnd",
                "blatMbEnd2016": "gnt:hasBlatMbEnd2016",
                "blatSeq": "gnt:hasBlatSeq",
                "targetSeq": "gnt:hasTargetSeq",
                "homologene": "gnt:hasHomologeneId",
                "uniprot": "gnt:hasUniprotId",
                "pubchem": "gnt:hasPubChemId",
                "kegg": "gnt:hasKeggId",
                "omim": "gnt:hasOmimId",
                "chebi": "gnt:hasChebiId",
            },
        }
        return query_and_compact(
            _query, _context,
            current_app.config.get("SPARQL_ENDPOINT")
        )
    except (RemoteDisconnected, URLError):
        return jsonify({})
