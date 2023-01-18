"""Search using Xapian index."""

from collections import namedtuple
import gzip
import json
from functools import partial, reduce
from pathlib import Path
from typing import Callable
import urllib.parse

from flask import abort, Blueprint, current_app, jsonify, request
from pymonad.maybe import Just, Maybe, Nothing
from pymonad.tools import curry
import xapian

from gn3.monads import MonadicDict
from gn3.db_utils import xapian_database

search = Blueprint("search", __name__)

ChromosomalPosition = namedtuple("ChromosomalPosition", "chromosome position")
ChromosomalInterval = namedtuple("ChromosomalInterval", "chromosome start end")
IntervalLiftoverFunction = Callable[[ChromosomalInterval], Maybe[ChromosomalInterval]]
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


def query_subqueries(query: xapian.Query) -> list[xapian.Query]:
    """Return list of child queries in query."""
    return [query.get_subquery(i) for i in range(query.get_num_subqueries())]


def query_terms(query: xapian.Query) -> list[str]:
    """Return list of terms in query."""
    # Unfortunately, the TermIterator from python xapian bindings seems
    # buggy. So, we resort to traversing the query tree.
    # python xapian bindings do not expose xapian.Query.LEAF_TERM. This is
    # most likely a bug.
    leaf_type = 100
    if query.get_type() == leaf_type:
        # We have no choice but to access the protected _get_terms_begin method.
        # pylint: disable=protected-access
        return [query._get_terms_begin().get_term().decode("utf-8")]
    else:
        return reduce(lambda result, subquery: result + query_terms(subquery),
                      query_subqueries(query),
                      [])


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


def field_processor_or(*field_processors: FieldProcessorFunction) -> FieldProcessorFunction:
    """Combine field processors using the OR operator."""
    return (lambda query:
            combine_queries(xapian.Query.OP_OR,
                            *[field_processor(query)
                              for field_processor in field_processors]))


def liftover(chain_file: Path, position: ChromosomalPosition) -> Maybe[ChromosomalPosition]:
    """Liftover chromosomal position using chain file."""
    # The chain file format is described at
    # https://genome.ucsc.edu/goldenPath/help/chain.html
    def split_chain_line(line: str) -> tuple[ChromosomalInterval, ChromosomalInterval, int, str]:
        (_, _, target_chromosome, _, _, target_start, target_end,
         query_chromosome, query_size, query_strand, query_start, query_end, _) = line.split()
        return (ChromosomalInterval(target_chromosome.removeprefix("chr"),
                                    int(target_start), int(target_end)),
                ChromosomalInterval(query_chromosome.removeprefix("chr"),
                                    int(query_start), int(query_end)),
                int(query_size), query_strand)

    with gzip.open(chain_file, "rt") as file:
        for line in file:
            if line.startswith('chain'):
                (target, query, query_size, query_strand) = split_chain_line(line)
                if (target.chromosome == position.chromosome
                    and target.start <= position.position < target.end):
                    transformed_position = query.start + position.position - target.start
                    if query_strand == '-':
                        transformed_position = query_size - 1 - transformed_position
                    return Just(ChromosomalPosition(query.chromosome, transformed_position))
    return Nothing


def liftover_interval(chain_file: str, interval: ChromosomalInterval) -> ChromosomalInterval:
    """
    Liftover interval using chain file.

    This function lifts over the interval by merely lifting the start and end
    points. This is simplistic and not strictly correct, but will do for the
    purposes of synteny in search.
    """
    point_liftover = partial(liftover, chain_file)
    return (Maybe.apply(curry(2,
                              lambda start, end:
                              ChromosomalInterval(start.chromosome,
                                                  Just(start.position),
                                                  Just(end.position))))
            .to_arguments(interval_start(interval).bind(point_liftover),
                          interval_end(interval).bind(point_liftover))
            # In '-' strands, the order of the interval may be reversed. Work
            # around.
            # KLUDGE: Inspecting the value contained in a monad is usually bad
            # practice. But, in this case, there doesn't seem to be a way
            # around.
            .map(lambda interval: ChromosomalInterval(interval.chromosome,
                                              Just(min(interval.start.value, interval.end.value)),
                                              Just(max(interval.start.value, interval.end.value)))
                 if interval.start.is_just() and interval.end.is_just()
                 else interval))


def parse_range(range_string: str) -> tuple[Maybe[str], Maybe[str]]:
    """Parse xapian range strings such as start..end."""
    start, end = range_string.split("..")
    return (Nothing if start == "" else Just(start),
            Nothing if end == "" else Just(end))


def apply_si_suffix(location: str) -> int:
    """Apply SI suffixes kilo, mega, giga and convert to bases."""
    suffixes = {"k": 3, "m": 6, "g": 9}
    return int(float(location[:-1])*10**suffixes.get(location[-1].lower(), 0))


def parse_location_field(lifted_species: str, species_prefix: str,
                         chromosome_prefix: str, location_slot: int,
                         liftover_function: IntervalLiftoverFunction,
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

    def make_query(species: str, interval: ChromosomalInterval) -> xapian.Query:
        # TODO: Convert the xapian index to use bases instead of megabases.
        to_megabases = lambda x: str(float(x)/1e6)
        return combine_queries(xapian.Query.OP_AND,
                               xapian.Query(species_prefix + species),
                               xapian.Query(chromosome_prefix + interval.chromosome),
                               xapian.NumberRangeProcessor(location_slot)
                               (interval.start.maybe("", to_megabases),
                                interval.end.maybe("", to_megabases)))

    try:
        interval = split_query(query.decode("utf-8"))
    except ValueError:
        return xapian.Query(xapian.Query.OP_INVALID)
    return (liftover_function(interval)
            .maybe(xapian.Query.MatchNothing,
                   partial(make_query, lifted_species)))


def parse_synteny_field(synteny_prefix: str, query: bytes) -> xapian.Query:
    """Parse synteny field and return a xapian query."""
    if query.decode("utf-8") in ["on", "off"]:
        return xapian.Query(synteny_prefix + query.decode("utf-8"))
    else:
        return xapian.Query(xapian.Query.OP_INVALID)


def is_synteny_on(synteny_prefix: str, query: xapian.Query) -> bool:
    """Check if synteny search is requested in query."""
    return synteny_prefix + "on" in query_terms(query)


def remove_synteny_field(synteny_prefix: str, query: xapian.Query,
                         parent_operator: int = xapian.Query.OP_AND) -> xapian.Query:
    """Return a new query with the synteny field removed."""
    # Note that this function only supports queries that exclusively use the
    # AND, OR, FILTER, WEIGHT, RANGE and INVALID operators.
    # python xapian bindings do not expose xapian.Query.LEAF_TERM. This is
    # most likely a bug.
    leaf_type = 100
    # Handle leaf node.
    if query.get_type() == leaf_type:
        if not any(term.startswith(synteny_prefix) for term in query_terms(query)):
            return query
        elif parent_operator in [xapian.Query.OP_AND, xapian.Query.OP_FILTER]:
            return xapian.Query.MatchAll
        elif parent_operator == xapian.Query.OP_OR:
            return xapian.Query.MatchNothing
        else:
            raise ValueError("Unexpected operator in query", query.get_type())
    # Recurse on non-leaf nodes with the AND, OR or FILTER operators as root.
    elif query.get_type() in (xapian.Query.OP_AND, xapian.Query.OP_OR,
                              xapian.Query.OP_FILTER, xapian.Query.OP_SCALE_WEIGHT):
        return combine_queries(query.get_type(),
                               *[remove_synteny_field(synteny_prefix, subquery, query.get_type())
                                 for subquery in query_subqueries(query)])
    # Return other supported non-leaf nodes verbatim.
    elif query.get_type() in [xapian.Query.OP_VALUE_RANGE, xapian.Query.OP_INVALID]:
        return query
    # Raise an exception on unsupported non-leaf nodes.
    else:
        raise ValueError("Unexpected operator in query", query.get_type())


def parse_query(synteny_files_directory: Path, query: str):
    """Parse search query using GeneNetwork specific field processors."""
    synteny_prefix = "XSYN"

    def make_query_parser(synteny: bool) -> xapian.QueryParser:
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
        queryparser.add_prefix("synteny", FieldProcessor(partial(parse_synteny_field,
                                                                 synteny_prefix)))
        range_prefixes = ["mean", "peak", "mb", "peakmb", "additive", "year"]
        for i, prefix in enumerate(range_prefixes):
            queryparser.add_rangeprocessor(xapian.NumberRangeProcessor(i, prefix + ":"))

        # Add field processors for location shorthands.
        species_shorthands = {"Hs": "human",
                              "Mm": "mouse"}
        for shorthand, species in species_shorthands.items():
            field_processors = [partial(parse_location_field,
                                        species,
                                        species_prefix,
                                        chromosome_prefix,
                                        range_prefixes.index("mb"),
                                        Just)]
            # If human and synteny is requested, add liftover.
            # With synteny search, we search for the same gene sequences
            # across different species. But, the same gene sequences may be
            # present in very different chromosomal positions in different
            # species. So, we first liftover.
            if shorthand == "Hs" and synteny:
                chain_files = {"mouse": "hg19ToMm10-chains.over.chain.gz"}
                for lifted_species, chain_file in chain_files.items():
                    field_processors.append(
                        partial(parse_location_field,
                                lifted_species,
                                species_prefix,
                                chromosome_prefix,
                                range_prefixes.index("mb"),
                                partial(liftover_interval,
                                        synteny_files_directory / chain_file)))
            queryparser.add_boolean_prefix(
                shorthand,
                FieldProcessor(field_processor_or(*field_processors)))
        return queryparser

    return remove_synteny_field(
        synteny_prefix,
        make_query_parser(is_synteny_on(synteny_prefix,
                                        make_query_parser(False).parse_query(query)))
        .parse_query(query))


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

    query = parse_query(Path(current_app.config["DATA_DIR"]) / "synteny", querystring)
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
