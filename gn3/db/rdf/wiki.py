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
    "pubmed_id": "dct:references",
    "email": "foaf:mbox",
    "initial": "gnt:initial",
    "comment": "rdfs:comment",
    "created": "dct:created",
    "id": "dct:identifier",
    # This points to the RDF Node which is the unique identifier
    # for this triplet.  It's constructed using the comment-id and
    # the comment-versionId
    "wiki_identifier": "@id",
}


def get_wiki_entries_by_symbol(symbol: str, sparql_uri: str) -> dict:
    """Fetch all the Wiki entries using the symbol"""
    # This query uses a sub-query to fetch the latest comment by the
    # version id.
    query = Template("""
$prefix

CONSTRUCT {
    ?uid rdfs:label ?symbolName;
         gnt:reason ?reason ;
         gnt:species ?species ;
         dct:references ?pmid ;
         foaf:homepage ?weburl ;
         rdfs:comment ?comment ;
         foaf:mbox ?email ;
         gnt:initial ?usercode ;
         gnt:belongsToCategory ?category ;
         gnt:hasVersion ?versionId ;
         dct:created ?created ;
         dct:identifier ?identifier .
} WHERE {
    ?symbolId rdfs:label ?symbolName .
    ?uid rdfs:comment ?comment ;
         gnt:symbol ?symbolId ;
         rdf:type gnc:GNWikiEntry ;
         dct:created ?createTime .
    FILTER ( LCASE(?symbolName) = LCASE('$symbol') ) .
    {
        SELECT (MAX(?vers) AS ?max) ?id_ WHERE {
            ?symbolId rdfs:label ?symbolName .
            ?uid dct:identifier ?id_ ;
                 dct:hasVersion ?vers ;
                 dct:identifier ?id_ ;
                 gnt:symbol ?symbolId .
            FILTER ( LCASE(?symbolName) = LCASE('$symbol') ) .
        }
    }
    ?uid dct:hasVersion ?max ;
         dct:identifier ?id_ .
    OPTIONAL { ?uid gnt:reason ?reason } .
    OPTIONAL {
        ?uid gnt:belongsToSpecies ?speciesId .
        ?speciesId gnt:shortName ?species .
    } .
    OPTIONAL { ?uid dct:references ?pubmedId . } .
    OPTIONAL { ?uid foaf:homepage ?weburl . } .
    OPTIONAL { ?uid gnt:initial ?usercode . } .
    OPTIONAL { ?uid foaf:mbox ?email . } .
    OPTIONAL { ?uid gnt:belongsToCategory ?category . } .
    BIND (str(?version) AS ?versionId) .
    BIND (str(?id_) AS ?identifier) .
    BIND (str(?pubmedId) AS ?pmid) .
    BIND (str(?createTime) AS ?created) .
}
""").substitute(prefix=RDF_PREFIXES, symbol=symbol,)
    results = query_frame_and_compact(
        query, WIKI_CONTEXT,
        sparql_uri
    )
    data = results.get("data")
    if not data:
        return results
    return results


def get_comment_history(comment_id: int, sparql_uri: str) -> dict:
    """Get all the historical data for a given id"""
    query = Template("""
$prefix

CONSTRUCT {
    ?uid rdfs:label ?symbolName ;
         gnt:reason ?reason ;
         gnt:species ?species ;
         dct:references ?pmid ;
         foaf:homepage ?weburl ;
         rdfs:comment ?comment ;
         foaf:mbox ?email ;
         gnt:initial ?usercode ;
         gnt:belongsToCategory ?category ;
         gnt:hasVersion ?versionId ;
         rdf:type gnc:GNWikiEntry ;
         dct:created ?created .
} WHERE {
    ?symbolId rdfs:label ?symbolName .
    ?uid rdf:type gnc:GNWikiEntry ;
         rdfs:comment ?comment ;
         gnt:symbol ?symbolId ;
         dct:created ?createTime ;
         dct:hasVersion ?version ;
         dct:identifier $comment_id ;
         dct:identifier ?id_ .
    OPTIONAL { ?uid gnt:reason ?reason } .
    OPTIONAL {
        ?uid gnt:belongsToSpecies ?speciesId .
        ?speciesId gnt:shortName ?species .
    } .
    OPTIONAL { ?uid dct:references ?pubmedId . } .
    OPTIONAL { ?uid foaf:homepage ?weburl . } .
    OPTIONAL { ?uid gnt:initial ?usercode . } .
    OPTIONAL { ?uid foaf:mbox ?email . } .
    OPTIONAL { ?uid gnt:belongsToCategory ?category . } .
    BIND (str(?version) AS ?versionId) .
    BIND (str(?pubmedId) AS ?pmid) .
    BIND (str(?createTime) AS ?created) .
} ORDER BY DESC(?version) DESC(?createTime)
""").substitute(prefix=RDF_PREFIXES, comment_id=comment_id)
    results = query_frame_and_compact(
        query, WIKI_CONTEXT,
        sparql_uri
    )
    return results
