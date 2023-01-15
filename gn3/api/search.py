"""Search using Xapian index."""

from collections import namedtuple
import json
from functools import partial, reduce
from typing import Callable
import urllib.parse

from flask import abort, Blueprint, current_app, jsonify, request
from pymonad.maybe import Just, Maybe, Nothing
import xapian

from gn3.monads import MonadicDict
from gn3.db_utils import xapian_database

search = Blueprint("search", __name__)

ChromosomalPosition = namedtuple("ChromosomalPosition", "chromosome position")
ChromosomalInterval = namedtuple("ChromosomalInterval", "chromosome start end")
FieldProcessorFunction = Callable[[str], xapian.Query]


def interval_start(interval: ChromosomalInterval) -> Maybe[ChromosomalPosition]:
    """Return start of a ChromosomalInterval as a ChromosomalPosition."""
    return interval.start.map(lambda start: ChromosomalPosition(interval.chromosome, start))


def interval_end(interval: ChromosomalInterval) -> Maybe[ChromosomalPosition]:
    """Return end of a ChromosomalInterval as a ChromosomalPosition."""
    return interval.end.map(lambda end: ChromosomalPosition(interval.chromosome, end))


def combine_queries(operator: int, *queries: xapian.Query) -> xapian.Query:
    """Combine xapian queries using operator."""
    return reduce(partial(xapian.Query, operator), queries)


class FieldProcessor(xapian.FieldProcessor):
    """
    Field processor for use in a xapian query parser.

    This class allows us to create any field processor without creating a
    separate class for each. To create a field processor, you only have to
    pass FieldProcessor a function. This function may be a closure. All
    additional state required by the field processor is contained in the
    lexical environment of the closure.
    """
    def __init__(self, proc: FieldProcessorFunction) -> None:
        super().__init__()
        self.proc = proc
    def __call__(self, query: str) -> xapian.Query:
        return self.proc(query)


def parse_range(range_string: str) -> tuple[Maybe[str], Maybe[str]]:
    """Parse xapian range strings such as start..end."""
    start, end = range_string.split("..")
    return (Nothing if start == "" else Just(start),
            Nothing if end == "" else Just(end))


def apply_si_suffix(location: str) -> int:
    """Apply SI suffixes kilo, mega, giga and convert to bases."""
    suffixes = {"k": 3, "m": 6, "g": 9}
    return int(float(location[:-1])*10**suffixes.get(location[-1].lower(), 0))


def parse_location_field(species: str, species_prefix: str,
                         chromosome_prefix: str, location_slot: int,
                         query: bytes) -> xapian.Query:
    """Parse location shorthands and return a xapian query.

    Location shorthands compress species, chromosome and position into a
    single field. e.g., Hs:chr2:1M..1.2M
    """
    def split_query(query: str) -> ChromosomalInterval:
        """Split query into chromosome and location tuple."""
        chromosome, location = query.lower().split(":")
        if not chromosome.startswith("chr"):
            raise ValueError
        return ChromosomalInterval(chromosome.removeprefix("chr"),
                                   *[location.map(apply_si_suffix)
                                     for location in parse_range(location)])


    try:
        interval = split_query(query.decode("utf-8"))
    except ValueError:
        return xapian.Query(xapian.Query.OP_INVALID)
    return combine_queries(xapian.Query.OP_AND,
                           xapian.Query(species_prefix + species),
                           xapian.Query(chromosome_prefix + interval.chromosome),
                           xapian.NumberRangeProcessor(location_slot)
                           (interval.start.maybe("", str),
                            interval.end.maybe("", str)))


def parse_query(query: str):
    """Parse search query using GeneNetwork specific field processors."""
    queryparser = xapian.QueryParser()
    queryparser.set_stemmer(xapian.Stem("en"))
    queryparser.set_stemming_strategy(queryparser.STEM_SOME)
    species_prefix = "XS"
    chromosome_prefix = "XC"
    queryparser.add_boolean_prefix("author", "A")
    queryparser.add_boolean_prefix("species", species_prefix)
    queryparser.add_boolean_prefix("group", "XG")
    queryparser.add_boolean_prefix("tissue", "XI")
    queryparser.add_boolean_prefix("dataset", "XDS")
    queryparser.add_boolean_prefix("symbol", "XY")
    queryparser.add_boolean_prefix("chr", chromosome_prefix)
    queryparser.add_boolean_prefix("peakchr", "XPC")
    queryparser.add_prefix("description", "XD")
    range_prefixes = ["mean", "peak", "mb", "peakmb", "additive", "year"]
    for i, prefix in enumerate(range_prefixes):
        queryparser.add_rangeprocessor(xapian.NumberRangeProcessor(i, prefix + ":"))

    # Add field processors for location shorthands.
    species_shorthands = {"Hs": "human",
                          "Mm": "mouse",
                          "Rn": "rat"}
    for shorthand, species in species_shorthands.items():
        queryparser.add_boolean_prefix(
            shorthand, FieldProcessor(partial(parse_location_field,
                                              species,
                                              species_prefix,
                                              chromosome_prefix,
                                              range_prefixes.index("mb"))))
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
