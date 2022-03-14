import sys
import json
import traceback
from argparse import ArgumentParser

from gn3.db_utils import database_connector
from gn3.responses.pcorrs_responses import OutputEncoder
from gn3.computations.partial_correlations import partial_correlations_entry

def process_cli_arguments():
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
        type=str)
    parser.add_argument(
        "target_database",
        help="The target database to run the partial correlations against",
        type=str)
    parser.add_argument(
        "--criteria",
        help="Number of results to return",
        type=int, default=500)
    return parser.parse_args()

def cleanup_string(the_str):
    return the_str.strip('"\t\n\r ')

def run_partial_corrs(args):
    with database_connector() as conn:
        try:
            return partial_correlations_entry(
                conn, cleanup_string(args.primary_trait),
                tuple(cleanup_string(args.control_traits).split(",")),
                cleanup_string(args.method), args.criteria,
                cleanup_string(args.target_database))
        except Exception as exc:
            print(traceback.format_exc(), file=sys.stderr)
            return {
                "status": "exception",
                "message": traceback.format_exc()
            }

def enter():
    args = process_cli_arguments()
    print(json.dumps(
        run_partial_corrs(process_cli_arguments()),
        cls = OutputEncoder))

if __name__ == "__main__":
    enter()
