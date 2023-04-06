"""Script to run partial correlations"""

import json
import traceback
from argparse import ArgumentParser

from gn3.db_utils import database_connection
from gn3.responses.pcorrs_responses import OutputEncoder
from gn3.computations.partial_correlations import (
    partial_correlations_with_target_db,
    partial_correlations_with_target_traits)

def cleanup_string(the_str):
    "Remove tab, newline and carriage return characters."
    return the_str.strip('"\t\n\r ')

def process_common_args(args):
    "Process the common CLI arguments to a form usable by the functions"
    return {
        "primary_trait_name": cleanup_string(args.primary_trait),
        "control_trait_names": tuple(
            cleanup_string(args.control_traits).split(",")),
        "method": cleanup_string(args.method)
    }

def process_trait_args(args):
    """Process arguments to a form usable by the
    `partial_correlations_with_target_traits` function."""
    return {
        **process_common_args(args),
        "target_trait_names": tuple(
            cleanup_string(args.target_traits).split(","))
    }

def process_db_args(args):
    """Process arguments for the `partial_correlations_with_target_db`
    function."""
    return {
        **process_common_args(args),
        "target_db_name": cleanup_string(args.target_database),
        "criteria": args.criteria
    }

def pcorrs_against_traits(dbconn, args):
    """Run partial correlations agaist selected traits."""
    return partial_correlations_with_target_traits(
        dbconn, **process_trait_args(args))

def pcorrs_against_db(dbconn, args):
    """Run partial correlations agaist the entire dataset provided."""
    return partial_correlations_with_target_db(dbconn, **process_db_args(args))

def run_pcorrs(dbconn, args):
    """Run the selected partial correlations function."""
    try:
        return args.func(dbconn, args)
    except Exception as exc: # pylint: disable=[broad-except,unused-variable]
        return {
            "status": "exception",
            "message": traceback.format_exc()
        }

def against_traits_parser(parent_parser):
    """Parser for command to run partial correlations against selected traits"""
    parser = parent_parser.add_parser(
        "against-traits",
        help="Run partial correlations against a select list of traits")
    parser.add_argument(
        "target_traits",
        help=(
            "The target traits to run the partial correlations against. "
            "This is a comma-separated list of traits' fullnames, in the "
            "format <DATASET-NAME>::<TRAIT-NAME> e.g. "
            "UCLA_BXDBXH_CARTILAGE_V2::ILM103710672"),
        type=str)
    parser.set_defaults(func=pcorrs_against_traits)
    return parent_parser

def against_db_parser(parent_parser):
    """Parser for command to run partial correlations against entire dataset"""
    parser = parent_parser.add_parser(
        "against-db",
        help="Run partial correlations against an entire dataset")
    parser.add_argument(
        "target_database",
        help="The target database to run the partial correlations against",
        type=str)
    parser.add_argument(
        "--criteria",
        help="Number of results to return",
        type=int, default=500)
    parser.set_defaults(func=pcorrs_against_db)
    return parent_parser

def process_cli_arguments():
    """Top level parser"""
    parser = ArgumentParser()
    parser.add_argument(
        "primary_trait",
        help="The primary trait's full name",
        type=str)
    parser.add_argument(
        "control_traits",
        help="A comma-separated list of traits' full names",
        type=str)
    parser.add_argument(
        "method",
        help="The correlation method to use",
        type=str,
        choices=("pearsons", "spearmans"))
    parser.add_argument(
        "sql_uri",
        help="The uri to use to connect to the database",
        type=str)
    against_db_parser(against_traits_parser(
        parser.add_subparsers(
            title="subcommands",
            description="valid subcommands",
            required=True)))
    return parser.parse_args()

def main():
    """Entry point for the script"""
    args = process_cli_arguments()

    with database_connection(args.sql_uri) as conn:
        print(json.dumps(run_pcorrs(conn, args), cls=OutputEncoder))


if __name__ == "__main__":
    main()
