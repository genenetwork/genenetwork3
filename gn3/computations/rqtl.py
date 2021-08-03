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


def process_rqtl_mapping(file_name: str) -> List:
    """Given an output file name, read in R/qtl results and return
    a List of marker objects

    """
    marker_obs = []
    # Later I should probably redo this using csv.read to avoid the
    # awkwardness with removing quotes with [1:-1]
    with open(os.path.join(current_app.config.get("TMPDIR", "/tmp"),
                           "output", file_name), "r") as the_file:
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

def process_rqtl_pairscan(file_name: str) -> List:
    """Given an output file name, read in R/qtl pair-scan results and return
    a list of both the JSON needed for the d3panels figure and a list of results
    to be used when generating the results table (which will include marker names)

    """

    figure_data = pairscan_results_for_figure(file_name)
    table_data = pairscan_results_for_table(file_name)

    return [figure_data, table_data]

def pairscan_for_figure(file_name: str) -> Dict:
    """Given an output file name, read in R/qtl pair-scan results and return
    the JSON needed for the d3panels figure

    """
    figure_data = {}

    # Open the file with the actual results, written as a list of lists
    with open(os.path.join(current_app.config.get("TMPDIR", "/tmp"),
                           "output", file_name), "r") as the_file:
        lod_results = []
        for i, line in enumerate(the_file):
            if i == 0: # Skip first line
                continue
            line_items = [item.rstrip('\n') for item in line.split(",")]
            lod_results.append(line_items[1:]) # Append all but first item in line
        figure_data['lod'] = lod_results

    # Open the map file with the list of markers/pseudomarkers and their positions
    with open(os.path.join(current_app.config.get("TMPDIR", "/tmp"),
                           "output", "MAP_" + file_name), "r") as the_file:
        chr_list = []
        pos_list = []
        for i, line in enumerate(the_file):
            if i == 0: # Skip first line
                continue
            line_items = [item.rstrip('\n') for item in line.split(",")]
            chr_list.append(line_items[1])
            pos_list.append(line_items[2])
        figure_data['chr'] = chr_list
        figure_data['pos'] = pos_list

    return figure_data


def pairscan_for_table(file_name: str) -> List:
    """Given an output file name, read in R/qtl pair-scan results and return
    a list of results to be used when generating the results table (which will include marker names)

    """
    table_data = []

    # Open the map file with the list of markers/pseudomarkers and create list of marker obs
    with open(os.path.join(current_app.config.get("TMPDIR", "/tmp"),
                           "output", "MAP_" + file_name), "r") as the_file:
        marker_list = []
        for i, line in enumerate(the_file.readlines()[1:]):
            line_items = [item.rstrip('\n') for item in line.split(",")]
            this_marker = {
                'name': line_items[0],
                'chr': line_items[1][1:-1], # Strip quotes from beginning and end of chr string
                'pos': line_items[2]
            }

            marker_list.append(this_marker)

    # Open the file with the actual results and write the results as
    # they will be displayed in the results table
    with open(os.path.join(current_app.config.get("TMPDIR", "/tmp"),
                           "output", file_name), "r") as the_file:
        for i, line in enumerate(the_file.readlines()[1:]):
            marker_1 = marker_list[i]
            line_items = [item.rstrip('\n') for item in line.split(",")]
            for j, item in enumerate(line_items[1:]):
                marker_2 = marker_list[j]
                try:
                    lod_score = f"{float(item):.3f}"
                except:
                    lod_score = f"{item}"
                this_line = {
                    'marker1': f"{marker_1['name']}",
                    'pos1': f"Chr {marker_1['chr']} @ {float(marker_1['pos']):.1f} cM",
                    'lod': lod_score,
                    'marker2': f"{marker_2['name']}",
                    'pos2': f"Chr {marker_2['chr']} @ {float(marker_2['pos']):.1f} cM"
                }
            table_data.append(this_line)

    return table_data


def process_perm_output(file_name: str):
    """Given base filename, read in R/qtl permutation output and calculate
    suggestive and significant thresholds

    """
    perm_results = []
    with open(os.path.join(current_app.config.get("TMPDIR", "/tmp"),
                           "output", "PERM_" + file_name), "r") as the_file:
        for i, line in enumerate(the_file):
            if i == 0:
                # Skip header line
                continue

            line_items = line.split(",")
            perm_results.append(float(line_items[1]))

    suggestive = np.percentile(np.array(perm_results), 67)
    significant = np.percentile(np.array(perm_results), 95)

    return perm_results, suggestive, significant
