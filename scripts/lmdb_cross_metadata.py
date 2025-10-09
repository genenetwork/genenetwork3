"""
This script processes and dumps cross metadata to lmdb from  cross control file.
Example:
guix shell python-click python-lmdb python-wrapper   python-pyyaml
python python  dump_metadata.py  dump-cross [LMDB_PATH] [CROSS_FILE_PATH] --file-format  yaml/json
or
python  dump_metadata.py  dump-cross "./test_lmdb_data" "./cross_file.json"
"""

import json
import yaml
import csv
import lmdb
import click
from pathlib import Path
from pprint import pprint


def read_metadata(file_path: str, file_format: str = "") -> dict:
    """read metadata from file_path and decode json as dict"""
    file_path = Path(file_path)
    file_format = (file_format or file_path.suffix[1:]).lower()
    with open(file_path, "r") as file_handler:
        if file_format == "yaml":
            results = yaml.safe_load(file_handler)
        elif file_format == "json":
            results = json.load(file_handler)
        else:
            raise NotImplementedError(
                f"this file format {file_format} is not yet supported")
    if "cross_info" in results:
        results["cross_info_metadata"] = process_cross_info(
            results["cross_info"])
    # expects this to be relative to the cross file
    directory_path = Path(file_path).parent
    if "phenocovar" in results:
        results["phenocovar"] = parse_covariates(
            os.path.join(directory_path, results["phenocovar"]))
    if "covar" in results:
        results["covar"] = parse_covariates(
            os.path.join(directory_path, results["covar"]))
    return results


def skip_comments(file_object, comment_prefix="#"):
    """A generator that filters out line starting with a certain prefix"""
    for line in file_object:
        if not line.strip().startswith(comment_prefix):
            yield line.strip()


def parse_covariates(csv_file) -> dict:
    """Function to parse csv covariates file """
    with open(csv_file, "r") as file_handler:
        results = [{k: v for k, v in row.items()}
                   for row in csv.DictReader(skip_comments(file_handler), skipinitialspace=True)
                   ]
        return results


def create_database(db_path: str) -> lmdb.Environment:
    """Create or open an LMDB environment."""
    return lmdb.open(db_path, map_size=100 * 1024 * 1024 * 1024, create=False)


@click.command(help="Dump the cross metadata information to lmdb")
@click.argument(
    "lmdb_path",
    type=click.Path(exists=True, file_okay=False,
                    readable=True, path_type=str),
)
@click.argument("cross_file")
@click.option('--file-format', type=click.Choice(['json', 'yaml'],
                                                 case_sensitive=False),
              default=None,
              help="Cross file format ")
def dump_cross(lmdb_path: str, cross_file: str, file_format: str):
    """dump the cross metadata to lmdb """
    metadata = read_metadata(cross_file, file_format=file_format)
    with create_database(lmdb_path) as db:
        cross_metadata = json.dumps(metadata).encode("utf-8")
        with db.begin(write=True) as txn:
            # storing this separate from other metadata
            txn.put(b"cross_metadata", cross_metadata)


def process_cross_info(cross_info):
    """process cross_info from cross file and  // contains the cross_direction"""
    rows_dict = []
    with open(cross_info["file"]) as file_handler:
        lines = (line for line in file_handler if not line.strip().startswith("#"))
        for (idx, (cross_id, cross_direction)) in enumerate(csv.reader(lines)):
            if idx != 0:
                rows_dict.append(
                    {"id": cross_id, "cross_direction": cross_direction})
        cross_val = [(key, val) for key, val in cross_info.items() if key != "file" and isinstance(
            val, int)][0]  # representation of cross direction as int
        return {"cross_direction": rows_dict, "cross_val": cross_val}


@click.command(help="Print the lmdb cross metadata")
@click.argument(
    "lmdb_path",
    type=click.Path(exists=True, file_okay=False,
                    readable=True, path_type=str),
)
def print_cross(lmdb_path):
    """Nicely print the cross metadata Debug!"""
    with create_database(lmdb_path) as db:
        with db.begin(write=False) as txn:
            cross_metadata_bytes = txn.get(b"cross_metadata")
            pprint(f"Cross Metadata: {json.loads(cross_metadata_bytes)}",
                   indent=4)


@click.group()
def cli():
    pass


cli.add_command(dump_cross)
cli.add_command(print_cross)


if __name__ == "__main__":
    cli()
