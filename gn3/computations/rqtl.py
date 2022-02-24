"""Procedures related rqtl computations"""
import os
from typing import Dict, List, Union

import numpy as np

from flask import current_app

from gn3.commands import compose_rqtl_cmd
from gn3.computations.gemma import generate_hash_of_string
from gn3.fs_helpers import get_hash_of_files

def generate_rqtl_cmd(rqtl_wrapper_cmd: str,
                      rqtl_wrapper_kwargs: Dict,
                      rqtl_wrapper_bool_kwargs: list) -> Dict:
    """Given the base rqtl_wrapper command and
dict of keyword arguments, return the full rqtl_wrapper command and an
output filename generated from a hash of the genotype and phenotype files

    """

    # Generate a hash from contents of the genotype and phenotype files
    _hash = get_hash_of_files(
        [v for k, v in rqtl_wrapper_kwargs.items() if k in ["g", "p"]])

    # Append to hash a hash of keyword arguments
    _hash += generate_hash_of_string(
        ",".join([f"{k}:{v}" for k, v in rqtl_wrapper_kwargs.items() if k not in ["g", "p"]]))

    # Append to hash a hash of boolean keyword arguments
    _hash += generate_hash_of_string(
        ",".join(rqtl_wrapper_bool_kwargs))

    # Temporarily substitute forward-slashes in hash with underscores
    _hash = _hash.replace("/", "_")

    _output_filename = f"{_hash}-output.csv"
    rqtl_wrapper_kwargs["filename"] = _output_filename

    return {
        "output_file":
        _output_filename,
        "rqtl_cmd":
        compose_rqtl_cmd(rqtl_wrapper_cmd=rqtl_wrapper_cmd,
                         rqtl_wrapper_kwargs=rqtl_wrapper_kwargs,
                         rqtl_wrapper_bool_kwargs=rqtl_wrapper_bool_kwargs)
    }


def process_rqtl_output(file_name: str) -> List:
    """Given an output file name, read in R/qtl results and return
    a List of marker objects

    """
    marker_obs = []
    # Later I should probably redo this using csv.read to avoid the
    # awkwardness with removing quotes with [1:-1]
    with open(os.path.join(current_app.config.get("TMPDIR", "/tmp"),
                           "output", file_name), "r", encoding="utf-8") as the_file:
        for line in the_file:
            line_items = line.split(",")
            if line_items[1][1:-1] == "chr" or not line_items:
                # Skip header line
                continue

            # Convert chr to int if possible
            the_chr: Union[int, str]
            try:
                the_chr = int(line_items[1][1:-1])
            except ValueError:
                the_chr = line_items[1][1:-1]
            this_marker = {
                "name": line_items[0][1:-1],
                "chr": the_chr,
                "cM": float(line_items[2]),
                "Mb": float(line_items[2]),
                "lod_score": float(line_items[3])
            }
            marker_obs.append(this_marker)

    return marker_obs


def process_perm_output(file_name: str):
    """Given base filename, read in R/qtl permutation output and calculate
    suggestive and significant thresholds

    """
    perm_results = []
    with open(os.path.join(current_app.config.get("TMPDIR", "/tmp"),
                           "output", "PERM_" + file_name), "r", encoding="utf-8") as the_file:
        for i, line in enumerate(the_file):
            if i == 0:
                # Skip header line
                continue

            line_items = line.split(",")
            perm_results.append(float(line_items[1]))

    suggestive = np.percentile(np.array(perm_results), 67)
    significant = np.percentile(np.array(perm_results), 95)

    return perm_results, suggestive, significant
