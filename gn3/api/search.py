"""Search using Xapian index."""

import json
import urllib.parse

from flask import abort, Blueprint, current_app, jsonify, request
import xapian

from gn3.monads import MonadicDict
from gn3.db_utils import xapian_database

search = Blueprint("search", __name__)


def parse_query(query: str):
    """Parse search query using GeneNetwork specific field processors."""
    queryparser = xapian.QueryParser()
    queryparser.set_stemmer(xapian.Stem("en"))
    queryparser.set_stemming_strategy(queryparser.STEM_SOME)
    queryparser.add_boolean_prefix("author", "A")
    queryparser.add_boolean_prefix("species", "XS")
    queryparser.add_boolean_prefix("group", "XG")
    queryparser.add_boolean_prefix("tissue", "XI")
    queryparser.add_boolean_prefix("dataset", "XDS")
    queryparser.add_boolean_prefix("symbol", "XY")
    queryparser.add_boolean_prefix("chr", "XC")
    queryparser.add_boolean_prefix("peakchr", "XPC")
    queryparser.add_prefix("description", "XD")
    range_prefixes = ["mean", "peak", "mb", "peakmb", "additive", "year"]
    for i, prefix in enumerate(range_prefixes):
        queryparser.add_rangeprocessor(xapian.NumberRangeProcessor(i, prefix + ":"))
    return queryparser.parse_query(query)


@search.route("/")
def search_results():
    """Search Xapian index and return a list of results."""
    args = request.args
    search_type = args.get("type", default="gene")
    querystring = args.get("query", default="")
    page = args.get("page", default=1, type=int)
    if page < 1:
        abort(404, description="Requested page does not exist")
    results_per_page = args.get("per_page", default=100, type=int)
    maximum_results_per_page = 10000
    if results_per_page > maximum_results_per_page:
        abort(400, description="Requested too many search results")

    query = parse_query(querystring)
    traits = []
    # pylint: disable=invalid-name
    with xapian_database(current_app.config["XAPIAN_DB_PATH"]) as db:
        enquire = xapian.Enquire(db)
        # Filter documents by type.
        enquire.set_query(xapian.Query(xapian.Query.OP_FILTER,
                                       query,
                                       xapian.Query(f"XT{search_type}")))
        for xapian_match in enquire.get_mset((page-1)*results_per_page, results_per_page):
            trait = MonadicDict(json.loads(xapian_match.document.get_data()))
            # Add PubMed link to phenotype search results.
            if search_type == "phenotype":
                trait["pubmed_link"] = trait["pubmed_id"].map(
                    lambda pubmed_id: "http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?"
                    + urllib.parse.urlencode({"cmd": "Retrieve",
                                              "db": "PubMed",
                                              "list_uids": pubmed_id,
                                              "dopt": "Abstract"}))
            traits.append(trait.data)
    return jsonify(traits)
