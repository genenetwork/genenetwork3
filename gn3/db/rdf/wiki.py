"""Sparql queries to get metadata about WIKI and RIF metadata.

NOTE: In the CONSTRUCT queries below, we manually sort the arrays from
 the result of a CONSTRUCT.  This is because the SPARQL engine does
 not provide a guarantee that it will support an ORDER BY clause in a
 CONSTRUCT. Using ORDER BY on a solution sequence for a CONSTRUCT or
 DESCRIBE query has no direct effect because only SELECT returns a
 sequence of results.  See:
   <https://stackoverflow.com/questions/78186393>
   <https://www.w3.org/TR/rdf-sparql-query/#modOrderBy>
"""
from string import Template
from gn3.db.rdf import BASE_CONTEXT, RDF_PREFIXES, query_frame_and_compact


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


def __sanitize_result(result: dict) -> dict:
    """Make sure `categories` and `pubmed_ids` are always arrays"""
    if not result:
        return {}
    categories = result.get("categories")
    if isinstance(categories, str):
        result["categories"] = [categories] if categories else []
    pmids = result.get("pubmed_ids")
    if isinstance(pmids, str):
        result["pubmed_ids"] = [pmids] if pmids else []
    if isinstance(pmids, int):
        result["pubmed_ids"] = [pmids]
    result["pubmed_ids"] = [
        int(pmid.split("/")[-1]) if isinstance(pmid, str) else pmid
        for pmid in result["pubmed_ids"]
    ]
    return result


def get_wiki_entries_by_symbol(
    symbol: str, sparql_uri: str, graph: str = "<http://genenetwork.org>"
) -> dict:
    """Fetch all the Wiki entries using the symbol"""
    # This query uses a sub-query to fetch the latest comment by the
    # version id.
    query = Template(
        """
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
} FROM $graph WHERE {
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
"""
    ).substitute(
        prefix=RDF_PREFIXES,
        graph=graph,
        symbol=symbol,
    )
    results = query_frame_and_compact(query, WIKI_CONTEXT, sparql_uri)
    data = [__sanitize_result(result) for result in results.get("data", {})]
    # See note above in the doc-string
    results["data"] = sorted(data, key=lambda d: d["created"])
    if not data:
        return results
    return results


def get_comment_history(
    comment_id: int, sparql_uri: str, graph: str = "<http://genenetwork.org>"
) -> dict:
    """Get all the historical data for a given id"""
    query = Template(
        """
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
} FROM $graph WHERE {
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
"""
    ).substitute(prefix=RDF_PREFIXES, graph=graph, comment_id=comment_id)
    results = query_frame_and_compact(query, WIKI_CONTEXT, sparql_uri)
    data = [__sanitize_result(result) for result in results.get("data", {})]
    # See note above in the doc-string
    results["data"] = sorted(data, key=lambda d: d["version"], reverse=True)
    return results
