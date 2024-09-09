"""Sparql queries to get metadata about WIKI and RIF metadata.

"""
from string import Template
from gn3.db.rdf import (BASE_CONTEXT, RDF_PREFIXES,
                        query_frame_and_compact)


WIKI_CONTEXT = BASE_CONTEXT | {
    "foaf": "http://xmlns.com/foaf/0.1/",
    "dct": "http://purl.org/dc/terms/",
    "categories": "gnt:belongsToCategory",
    "web_url": "foaf:homepage",
    "version": "gnt:hasVersion",
    "symbol": "rdfs:label",
    "reason": "gnt:reason",
    "species": "gnt:species",
    "pubmed_ids": "dct:references",
    "email": "foaf:mbox",
    "initial": "gnt:initial",
    "comment": "rdfs:comment",
    "created": "dct:created",
    "id": "dct:identifier",
}


def get_wiki_entries_by_symbol(symbol: str, sparql_uri: str) -> dict:
    """Fetch all the Wiki entries using the symbol"""
    # This query uses a sub-query to fetch the latest comment by the
    # version id.
    query = Template("""
$prefix

CONSTRUCT {
    ?comment rdfs:label ?symbolName;
             gnt:reason ?reason ;
             gnt:species ?species ;
             dct:references ?pmid ;
             foaf:homepage ?weburl ;
             rdfs:comment ?text ;
             foaf:mbox ?email ;
             gnt:initial ?usercode ;
             gnt:belongsToCategory ?category ;
             gnt:hasVersion ?max ;
             dct:created ?created ;
             dct:identifier ?id_ .
} WHERE {
    ?symbolId rdfs:label ?symbolName .
    ?comment rdfs:label ?text_ ;
             gnt:symbol ?symbolId ;
             rdf:type gnc:GNWikiEntry ;
             dct:identifier ?id_ ;
             dct:created ?createTime .
    FILTER ( LCASE(?symbolName) = LCASE('$symbol') ) .
    {
        SELECT (MAX(?vers) AS ?max) ?id_ WHERE {
            ?comment dct:identifier ?id_ ;
                     dct:hasVersion ?vers .
        }
    }
    ?comment dct:hasVersion ?max .
    OPTIONAL { ?comment gnt:reason ?reason_ } .
    OPTIONAL {
        ?comment gnt:belongsToSpecies ?speciesId .
        ?speciesId gnt:shortName ?species .
    } .
    OPTIONAL { ?comment dct:references ?pmid_ } .
    OPTIONAL { ?comment foaf:homepage ?weburl_ } .
    OPTIONAL { ?comment gnt:initial ?usercode_ } .
    OPTIONAL { ?comment foaf:mbox ?email_ } .
    OPTIONAL { ?comment gnt:belongsToCategory ?category_ } .
    BIND (str(?createTime) AS ?created) .
    BIND (str(?text_) AS ?text) .
    BIND (str(?version) AS ?versionId) .
    BIND (STR(COALESCE(?pmid_, "")) AS ?pmid) .
    BIND (COALESCE(?reason_, "") AS ?reason) .
    BIND (STR(COALESCE(?weburl_, "")) AS ?weburl) .
    BIND (COALESCE(?usercode_, "") AS ?usercode) .
    BIND (STR(COALESCE(?email_, "")) AS ?email) .
    BIND (COALESCE(?species_, "") AS ?species) .
    BIND (COALESCE(?category_, "") AS ?category) .
}
""").substitute(prefix=RDF_PREFIXES, symbol=symbol,)
    results = query_frame_and_compact(
        query, WIKI_CONTEXT,
        sparql_uri
    )
    data = results.get("data")
    for result in data:
        categories = result.get("categories") or []
        if categories and isinstance(categories, str):
            result["categories"] = [categories]
        pmids = result.get("pubmed_ids")
        if pmids and isinstance(pmids, str):
            result["pubmed_ids"] = [pmids]
        elif pmids:
            result["pubmed_ids"] = [int(pmid.split("/")[-1]) for pmid in pmids]
        else:
            result["pubmed_ids"] = []
    results["data"] = sorted(data, key=lambda d: d["created"])
    if not data:
        return results
    return results


def get_comment_history(comment_id: int, sparql_uri: str) -> dict:
    """Get all the historical data for a given id"""
    query = Template("""
$prefix

CONSTRUCT {
    ?comment rdfs:label ?symbolName ;
             gnt:reason ?reason ;
             gnt:species ?species ;
             dct:references ?pmid ;
             foaf:homepage ?weburl ;
             rdfs:comment ?text ;
             foaf:mbox ?email ;
             gnt:initial ?usercode ;
             gnt:belongsToCategory ?category ;
             gnt:hasVersion ?version ;
             dct:created ?created .
} WHERE {
    ?symbolId rdfs:label ?symbolName .
    ?comment rdf:type gnc:GNWikiEntry ;
             rdfs:label ?text_ ;
             gnt:symbol ?symbolId ;
             dct:created ?createTime ;
             dct:hasVersion ?version ;
             dct:identifier $comment_id ;
             dct:identifier ?id_ .
    OPTIONAL { ?comment gnt:reason ?reason_ } .
    OPTIONAL {
        ?comment gnt:belongsToSpecies ?speciesId .
        ?speciesId gnt:shortName ?species_ .
    } .
    OPTIONAL { ?comment dct:references ?pmid_ . } .
    OPTIONAL { ?comment foaf:homepage ?weburl_ . } .
    OPTIONAL { ?comment gnt:initial ?usercode_ . } .
    OPTIONAL { ?comment foaf:mbox ?email_ . } .
    OPTIONAL { ?comment gnt:belongsToCategory ?category_ . } .
    BIND (str(?text_) AS ?text) .
    BIND (str(?createTime) AS ?created) .
    BIND (STR(COALESCE(?pmid_, "")) AS ?pmid) .
    BIND (COALESCE(?reason_, "") AS ?reason) .
    BIND (STR(COALESCE(?weburl_, "")) AS ?weburl) .
    BIND (COALESCE(?usercode_, "") AS ?usercode) .
    BIND (STR(COALESCE(?email_, "")) AS ?email) .
    BIND (COALESCE(?species_, "") AS ?species) .
    BIND (COALESCE(?category_, "") AS ?category) .
}
""").substitute(prefix=RDF_PREFIXES, comment_id=comment_id)
    results = query_frame_and_compact(
        query, WIKI_CONTEXT,
        sparql_uri
    )
    data = results.get("data")
    for result in data:
        categories = result.get("categories") or []
        if categories and isinstance(categories, str):
            result["categories"] = [categories]
        pmids = result.get("pubmed_ids")
        if pmids and isinstance(pmids, str):
            result["pubmed_ids"] = [pmids]
        elif pmids:
            result["pubmed_ids"] = [int(pmid.split("/")[-1]) for pmid in pmids]
        else:
            result["pubmed_ids"] = []
        result["version"] = int(result["version"])

    # We manually sort the array, since the SPARQL engine does not
    # provide a guarantee that it will support an ORDER BY clause in a
    # CONSTRUCT. Using ORDER BY on a solution sequence for a CONSTRUCT
    # or DESCRIBE query has no direct effect because only SELECT
    # returns a sequence of results.  See:
    # <https://stackoverflow.com/questions/78186393>
    # <https://www.w3.org/TR/rdf-sparql-query/#modOrderBy>
    results["data"] = sorted(data, key=lambda d: d["version"], reverse=True)
    return results
