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
from gn3.db.rdf import (
    BASE_CONTEXT,
    RDF_PREFIXES,
    query_frame_and_compact,
    update_rdf,
    sparql_query,
)


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
    result["categories"] = sorted(result["categories"])
    pmids = result.get("pubmed_ids")
    if isinstance(pmids, str):
        result["pubmed_ids"] = [pmids] if pmids else []
    if isinstance(pmids, int):
        result["pubmed_ids"] = [pmids]
    result["pubmed_ids"] = [
        int(pmid.split("/")[-1]) if isinstance(pmid, str) else pmid
        for pmid in result["pubmed_ids"]
    ]
    result["pubmed_ids"] = sorted(result["pubmed_ids"])
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
    ?comment rdfs:label ?symbol;
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
    ?comment rdfs:label ?text_ ;
             gnt:symbol ?symbol ;
             rdf:type gnc:GNWikiEntry ;
             dct:identifier ?id_ ;
             dct:created ?createTime .
    FILTER ( LCASE(STR(?symbol)) = LCASE("$symbol") ) .
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
        ?speciesId gnt:shortName ?species_ .
    } .
    OPTIONAL { ?comment dct:references ?pmid_ } .
    OPTIONAL { ?comment foaf:homepage ?weburl_ } .
    OPTIONAL { ?comment gnt:initial ?usercode_ } .
    OPTIONAL { ?comment foaf:mbox ?email_ } .
    OPTIONAL { ?comment gnt:belongsToCategory ?category_ } .
    BIND (str(?createTime) AS ?created) .
    BIND (str(?text_) AS ?text) .
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
    ?comment rdfs:label ?symbol ;
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
    ?comment rdf:type gnc:GNWikiEntry ;
             rdfs:label ?text_ ;
             gnt:symbol ?symbol ;
             dct:created ?createTime ;
             dct:hasVersion ?version ;
             dct:identifier $comment_id .
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


def update_wiki_comment(
        insert_dict: dict,
        sparql_user: str,
        sparql_password: str,
        sparql_auth_uri: str,
        graph: str = "<http://genenetwork.org>",
) -> str:
    """Update a wiki comment by inserting a comment with the same
identifier but an updated version id.
    """
    name = f"gn:wiki-{insert_dict['Id']}-{insert_dict['versionId']}"
    comment_triple = Template("""$name rdfs:label '''$comment'''@en ;
rdf:type gnc:GNWikiEntry ;
gnt:symbol "$symbol" ;
dct:identifier "$comment_id"^^xsd:integer ;
dct:hasVersion "$next_version"^^xsd:integer ;
dct:created "$created"^^xsd:datetime .
""").substitute(
        comment=insert_dict["comment"],
        name=name, symbol=insert_dict['symbol'],
        comment_id=insert_dict["Id"], next_version=insert_dict["versionId"],
        created=insert_dict["createtime"])
    using = ""
    if insert_dict["email"]:
        comment_triple += f"{name} foaf:mbox <{insert_dict['email']}> .\n"
    if insert_dict["initial"]:
        comment_triple += f"{name} gnt:initial \"{insert_dict['initial']}\" .\n"
    if insert_dict["species"]:
        comment_triple += f"{name} gnt:belongsToSpecies ?speciesId .\n"
        using = Template(
            """ USING $graph WHERE { ?speciesId gnt:shortName "$species" . } """).substitute(
                graph=graph, species=insert_dict["species"]
        )
    if insert_dict["reason"]:
        comment_triple += f"{name} gnt:reason \"{insert_dict['reason']}\" .\n"
    if insert_dict["weburl"]:
        comment_triple += f"{name} foaf:homepage <{insert_dict['weburl']}> .\n"
    for pmid in insert_dict["PubMed_ID"].split():
        comment_triple += f"{name} dct:references pubmed:{pmid} .\n"
    for category in insert_dict["categories"]:
        comment_triple += f'{name} gnt:belongsToCategory "{category}".\n'

    return update_rdf(
        query=Template(
            """
$prefix

INSERT {
GRAPH $graph {
$comment_triple}
} $using
""").substitute(prefix=RDF_PREFIXES,
                graph=graph,
                comment_triple=comment_triple,
                using=using),
        sparql_user=sparql_user,
        sparql_password=sparql_password,
        sparql_auth_uri=sparql_auth_uri,
    )


def get_rif_entries_by_symbol(
    symbol: str, sparql_uri: str, graph: str = "<http://genenetwork.org>"
) -> dict:
    """Fetch NCBI RIF entries for a given symbol (case-insensitive).

This function retrieves NCBI RIF entries using a SPARQL `SELECT` query
instead of a `CONSTRUCT` to avoid truncation.  The Virtuoso SPARQL
engine limits query results to 1,048,576 triples per solution, and
NCBI entries can exceed this limit.  Since there may be more than
2,000 entries, which could result in the number of triples surpassing
the limit, `SELECT` is used to ensure complete data retrieval without
truncation.  See:

<https://community.openlinksw.com/t/sparql-query-limiting-results-to-100000-triples/2131>

    """
    # XXX: Consider pagination
    query = Template(
        """
$prefix

SELECT ?comment ?symbol ?species ?pubmed_id ?version ?created ?gene_id ?taxonomic_id
FROM $graph WHERE {
    ?comment_id rdfs:label ?text_ ;
                gnt:symbol ?symbol ;
                rdf:type gnc:NCBIWikiEntry ;
                gnt:hasGeneId ?gene_id_ ;
                dct:hasVersion ?version ;
                dct:references ?pmid_ ;
                dct:created ?createTime ;
                gnt:belongsToSpecies ?speciesId .
    ?speciesId rdfs:label ?species .
    FILTER ( LCASE(?symbol) = LCASE("$symbol") ) .
    OPTIONAL { ?comment_id skos:notation ?taxonId_ . } .
    BIND (STR(?text_) AS ?comment) .
    BIND (xsd:integer(STRAFTER(STR(?taxonId_), STR(taxon:))) AS ?taxonomic_id) .
    BIND (xsd:integer(STRAFTER(STR(?pmid_), STR(pubmed:))) AS ?pubmed_id) .
    BIND (xsd:integer(STRAFTER(STR(?gene_id_), STR(generif:))) AS ?gene_id) .
    BIND (STR(?createTime) AS ?created) .
} ORDER BY ?species ?createTime
"""
    ).substitute(prefix=RDF_PREFIXES, graph=graph, symbol=symbol)
    results: dict[str, dict|list] = {
        "@context": {
            "dct": "http://purl.org/dc/terms/",
            "gnt": "http://genenetwork.org/term/",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "symbol": "gnt:symbol",
            "species": "gnt:species",
            "taxonomic_id": "skos:notation",
            "gene_id": "gnt:hasGeneId",
            "pubmed_id": "dct:references",
            "created": "dct:created",
            "comment": "rdfs:comment",
            "version": "dct:hasVersion",
        }
    }
    data: list[dict[str, int|str]] = []
    for entry in sparql_query(query=query, endpoint=sparql_uri, format_type="json"):
        data.append(
            {
                key: int(metadata.get("value"))
                if metadata.get("value").isdigit()
                else metadata.get("value")
                for key, metadata in entry.items()
            }
        )
    results["data"] = data
    return results
