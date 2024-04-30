"""API for fetching metadata using an API"""
import time

from string import Template
from pathlib import Path

from authlib.jose import jwt

from flask import Blueprint
from flask import request
from flask import current_app

from gn3.auth.authorisation.errors import AuthorisationError
from gn3.db.datasets import (retrieve_metadata,
                             save_metadata,
                             get_history)
from gn3.db.rdf import RDF_PREFIXES
from gn3.db.rdf import (query_frame_and_compact,
                        query_and_compact,
                        query_and_frame)


BASE_CONTEXT = {
    "data": "@graph",
    "id": "@id",
    "type": "@type",
    "gnc": "http://genenetwork.org/category/",
    "gnt": "http://genenetwork.org/term/",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
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

metadata = Blueprint("metadata", __name__)


@metadata.route("/datasets/<name>", methods=["GET"])
def datasets(name):
    """Fetch a dataset's metadata given it's ACCESSION_ID or NAME"""
    _query = Template("""
$prefix

CONSTRUCT {
          ?dataset ?predicate ?term ;
                   gnt:usesNormalization ?normalization .
          ?inbredSet rdfs:label ?inbredSetName .
          ?platform ?platformPred  ?platformObject .
          ?normalization rdfs:label ?normalizationName .
          ?tissue ?tissuePred ?tissueObj .
          ?investigator foaf:name ?investigatorName ;
                        foaf:homepage ?homepage .
          ?type skos:prefLabel ?altName .
} WHERE {
        ?dataset rdf:type dcat:Dataset ;
                  ?predicate ?term ;
                  (rdfs:label|dct:identifier|skos:prefLabel) "$name" .
        FILTER (!regex(str(?predicate), '(usesNormalization)', 'i')) .
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
          ?dataset gnt:usesNormalization ?normalization .
          ?normalization rdf:type gnc:avgMethod ;
                         rdfs:label ?normalizationName .
        } .
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
    __result = query_frame_and_compact(
        _query, _context,
        current_app.config.get("SPARQL_ENDPOINT")
    )
    return __result | retrieve_metadata(
        (Path(
            current_app.config.get("DATA_DIR")
        ) / "gn-docs/general/datasets" /
         Path(__result.get("id", "")).stem).as_posix()
    )


@metadata.route("/datasets/<group>/list", methods=["GET"])
def list_datasets_by_group(group):
    """List datasets that belong to a given group"""
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


@metadata.route("/datasets/<id_>/history")
def view_history(id_):
    """View a given dataset's history."""
    history = get_history(
        git_dir=Path(current_app.config.get("DATA_DIR"),
                     "gn-docs"),
        name=id_,
    ).either(
        lambda error: {
            "error": "Unable to fetch history",
            "error_description": error,
        },
        lambda history: {
            "id": id_,
            "history": history,
        })
    if history.get("error"):
        raise Exception(history.get("error_description"))
    return history


@metadata.route("/datasets/edit", methods=["POST"])
def edit_dataset():
    """Edit a given dataset"""
    # Fetch the public key
    key = ""
    with open(
            current_app.config.get("AUTH_SERVER_SSL_PUBLIC_KEY"), "rb"
    ) as _f:
        key = _f.read()

    # Decode the token
    payload = jwt.decode(
        request.headers.get("Authorization").split()[-1],  # the jwt token
        key  # the auth-server public key
    )

    # Validation:
    if payload.get("exp") - int(time.time()) > 300:
        raise AuthorisationError("Expired Token")
    if "group:resource:edit-resource" not in payload.get("roles", []):
        raise AuthorisationError("Insufficient Edit Privileges")
    gn_docs = Path(current_app.config["DATA_DIR"], "gn-docs")
    # This maps the form elements to the actual path in the git
    # repository
    map_ = {
        "description": "summary.rtf",
        "tissueInfo": "tissue.rtf",
        "specifics": "specifics.rtf",
        "caseInfo": "cases.rtf",
        "platformInfo": "platform.rtf",
        "processingInfo": "processing.rtf",
        "notes": "notes.rtf",
        "experimentDesignInfo": "experiment-design.rtf",
        "acknowledgement": "acknowledgement.rtf",
        "citation": "citation.rtf",
        "experimentType": "experiment-type.rtf",
        "contributors": "contributors.rtf"
    }
    output = Path(
        gn_docs,
        "general/datasets/",
        request.form.get("id").split("/")[-1],
        f"{map_.get(request.form.get('section'))}"
    )
    match request.form.get("type"):
        case "dcat:Dataset":
            author = f"{payload.get('account-name')} <{payload.get('email')}>"
            return save_metadata(
                git_dir=gn_docs,
                output=output,
                author=author,
                content=request.form.get("editor"),
                msg=request.form.get("edit-summary")
            ).either(
                lambda error: ({"error": error}, 500),
                lambda x: ("Edit successfull", 201)
            )

@metadata.route("/datasets/search/<term>", methods=["GET"])
def search_datasets(term):
    """Search datasets"""
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
        SELECT DISTINCT ?dataset ?label ?inbredSetName ?datasetType ?title
           WHERE {
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
        SELECT (COUNT(DISTINCT ?dataset)/$limit+1 AS ?pages)
            (COUNT(DISTINCT ?dataset) AS ?hits) WHERE {
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


@metadata.route("/publications/<name>", methods=["GET"])
def publications(name):
    """Fetch a publication's metadata given it's NAME"""
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


@metadata.route("/publications/search/<term>", methods=["GET"])
def search_publications(term):
    """Search publications"""
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


@metadata.route("/phenotypes/<name>", methods=["GET"])
@metadata.route("/phenotypes/<group>/<name>", methods=["GET"])
def phenotypes(name, group=None):
    """Fetch a phenotype's metadata given it's name"""
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


@metadata.route("/genotypes/<name>", methods=["GET"])
@metadata.route("/genotypes/<dataset>/<name>", methods=["GET"])
def genotypes(name, dataset=""):
    """Fetch a genotype's metadata given it's name"""
    _query = Template("""
$prefix

CONSTRUCT {
        ?genotype ?predicate ?object .
        ?genotype dcat:dataset ?dataset .
        ?species gnt:shortName ?speciesShortName .
        ?dataset rdfs:label ?datasetName ;
                 skos:prefLabel ?datasetFullName ;
                 gnt:belongsToGroup ?groupName .
} WHERE {
        ?genotype rdf:type gnc:Genotype ;
                  rdfs:label "$name" ;
                  ?predicate ?object .
        OPTIONAL {
            ?species ^gnt:belongsToSpecies ?genotype ;
                      gnt:shortName ?speciesShortName .
        } .
        OPTIONAL {
            ?dataset rdf:type dcat:Dataset ;
                     (rdfs:label|dct:identifier|skos:prefLabel) "$dataset" ;
                     rdfs:label ?datasetName ;
                     skos:prefLabel ?datasetFullName ;
                     gnt:belongsToGroup ?inbredSet .
            ?inbredSet rdfs:label ?groupName .
        } .
}
""").substitute(prefix=RDF_PREFIXES,
                name=name, dataset=dataset)
    _context = {
        "@context": BASE_CONTEXT | {
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "gnt": "http://genenetwork.org/term/",
            "xkos": "http://rdf-vocabulary.ddialliance.org/xkos#",
            "gnc": "http://genenetwork.org/category/",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "name": "rdfs:label",
            "chr": "gnt:chr",
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "prefLabel": "skos:prefLabel",
            "dcat": "http://www.w3.org/ns/dcat#",
            "dataset": "dcat:dataset",
            "mb": "gnt:mb",
            "mbMm8": "gnt:mbMm8",
            "mb2016": "gnt:mb2016",
            "sequence": "gnt:hasSequence",
            "source": "gnt:hasSource",
            "species": "gnt:belongsToSpecies",
            "speciesName": "gnt:shortName",
            "alternateSource": "gnt:hasAltSourceName",
            "comments": "rdfs:comments",
            "group": "gnt:belongsToGroup",
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


@metadata.route("/genewikis/gn/<symbol>", methods=["GET"])
def get_gn_genewiki_entries(symbol):
    """Fetch the GN and NCBI GeneRIF entries"""
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
    SELECT ?symbol ?comment
        (GROUP_CONCAT(DISTINCT ?speciesName; SEPARATOR='; ') AS ?species_)
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
    } GROUP BY ?comment ?symbol ?createTime
      ?creator ORDER BY ?createTime LIMIT $limit OFFSET $offset
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


@metadata.route("/genewikis/ncbi/<symbol>", methods=["GET"])
def get_ncbi_genewiki_entries(symbol):
    """Fetch the NCBI GeneRIF entries"""
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
    SELECT ?symbol ?comment ?geneId
         (GROUP_CONCAT(DISTINCT ?speciesName; SEPARATOR='; ') AS ?species_)
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
    } GROUP BY ?comment ?symbol ?createTime ?creator ?geneId
      ORDER BY ?createTime LIMIT $limit OFFSET $offset
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


@metadata.route("/species", methods=["GET"])
def list_species():
    """List all species"""
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


@metadata.route("/species/<name>", methods=["GET"])
def fetch_species(name):
    """Fetch a Single species information"""
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


@metadata.route("/groups", methods=["GET"])
def groups():
    """Fetch the list of groups"""
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


@metadata.route("/groups/<name>", methods=["GET"])
def fetch_group_by_species(name):
    """Fetch the list of groups (I.e. Inbredsets)"""
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


@metadata.route("/probesets/<name>", methods=["GET"])
@metadata.route("/probesets/<dataset>/<name>", methods=["GET"])
def probesets(name, dataset=""):
    """Fetch a probeset's metadata given it's name"""
    _query = Template("""
$prefix

CONSTRUCT {
        ?probeset ?predicate ?object ;
                  dct:references ?probesetResource ;
                  dct:references ?resource ;
                  gnt:belongsToSpecies ?speciesShortName ;
                  gnt:belongsToGroup ?groupName ;
                  gnt:hasTissue ?tissueName ;
                  gnt:belongsToDataset ?datasetFullName .
 ?resource rdfs:label ?resourceLabel ;
                  rdfs:comments ?resourceComments .
        ?probesetResource rdfs:label ?probesetResourceLabel ;
                          rdfs:comments ?probesetResourceComments .
        ?chip rdfs:label ?chipName .
} WHERE {
        ?probeset rdf:type gnc:Probeset ;
                  rdfs:label "$name" ;
                  ?predicate ?object .
        FILTER (!regex(str(?genePred), '(geneSymbol)', 'i')) .
        OPTIONAL {
           ?probeset gnt:geneSymbol ?symbolName .
           ?gene gnt:geneSymbol ?symbolName ;
                 rdf:type gnc:Gene .
           ?resource ^dct:references ?gene ;
                     a ?resourceLink .
           ?resourceLink rdfs:Class gnc:ResourceLink ;
                         rdfs:label ?resourceLabel ;
                         rdfs:comments ?resourceComments .
        } .
        OPTIONAL {
            ?probeset gnt:hasChip ?chip .
            ?chip rdfs:label ?chipName .
        } .
        OPTIONAL {
            ?probesetResource ^dct:references ?probeset ;
                              a ?probesetResourceLink .
            ?probesetResourceLink rdfs:label ?probesetResourceLabel ;
                                  rdfs:comments ?probesetResourceComments .
        } .
        OPTIONAL {
            ?dataset rdf:type dcat:Dataset ;
                 (rdfs:label|dct:identifier|skos:prefLabel) "$dataset" ;
                 (skos:altLabel|skos:prefLabel) ?datasetFullName .
        } .
        OPTIONAL {
                ?dataset gnt:hasTissue ?tissue .
                ?tissue rdfs:label ?tissueName .
        } .
        OPTIONAL {
                ?inbredSet ^skos:member gnc:Set ;
                           ^gnt:belongsToGroup ?dataset ;
                           rdfs:label ?groupName ;
                           xkos:generalizes ?species .
                ?species gnt:shortName ?speciesShortName .
        } .
}
""").substitute(prefix=RDF_PREFIXES, name=name, dataset=dataset)
    _context = {
        "@context": BASE_CONTEXT | {
            "alias": "skos:altLabel",
            "alignID": "gnt:hasAlignID",
            "blatMbEnd": "gnt:hasBlatMbEnd",
            "blatMbStart": "gnt:hasBlatMbStart",
            "blatScore": "gnt:hasBlatScore",
            "blatSeq": "gnt:hasBlatSeq",
            "chip": "gnt:hasChip",
            "chr": "gnt:chr",
            "chromosome": "gnt:chromosome",
            "comments": "rdfs:comments",
            "dct": "http://purl.org/dc/terms/",
            "description": "dct:description",
            "geneID": "gnt:hasGeneId",
            "group": "gnt:belongsToGroup",
            "dataset": "gnt:belongsToDataset",
            "tissue": "gnt:hasTissue",
            "kgID": "gnt:hasKgID",
            "location": "gnt:location",
            "mb": "gnt:mb",
            "name": "rdfs:label",
            "proteinID": "gnt:hasProteinID",
            "references": "dct:references",
            "rgdID": "gnt:hasRgdID",
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "species": "gnt:belongsToSpecies",
            "specificity": "gnt:hasSpecificity",
            "strand": "gnt:Strand",
            "strandProbe": "gnt:strandProbe",
            "symbol": "gnt:geneSymbol",
            "targetID": "gnt:hasTargetId",
            "targetRegion": "gnt:targetsRegion",
            "targetSequence": "gnt:hasTargetSeq",
            "transcript": "gnt:transcript",
            "txEnd": "gnt:TxEnd",
            "txStart": "gnt:TxStart",
            "unigenID": "gnt:hasUnigenID",
            "uniprot": "gnt:uniprot",
        },
        "probeset": {
            "type": "gnc:Probeset",
        },
        "type": "gnc:Probeset",
    }
    return query_frame_and_compact(
        _query, _context,
        current_app.config.get("SPARQL_ENDPOINT")
    )
