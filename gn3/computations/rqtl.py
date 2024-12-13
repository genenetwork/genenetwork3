"""Procedures related to R/qtl computations"""
import os
from bisect import bisect
from typing import Dict, List, Tuple, Union

import numpy as np

from flask import current_app

from gn3.commands import compose_rqtl_cmd
from gn3.computations.gemma import generate_hash_of_string
from gn3.fs_helpers import get_hash_of_files, assert_path_exists, get_tmpdir

from gn3.debug import __pk__

def generate_rqtl_cmd(
    rqtl_wrapper_cmd: str,
    rqtl_wrapper_kwargs: Dict,
    rqtl_wrapper_bool_kwargs: list,
) -> Dict:
    """Given the base rqtl_wrapper command and
    dict of keyword arguments, return the full rqtl_wrapper command and an
    output filename generated from a hash of the genotype and phenotype files"""

    assert_path_exists(rqtl_wrapper_cmd)

    # Generate a hash from contents of the genotype and phenotype files
    _hash = get_hash_of_files(
        [v for k, v in rqtl_wrapper_kwargs.items() if k in ["g", "p"]]
    )

    # Append to hash a hash of keyword arguments
    _hash += generate_hash_of_string(
        ",".join(
            [
                f"{k}:{v}"
                for k, v in rqtl_wrapper_kwargs.items()
                if k not in ["g", "p"]
            ]
        )
    )

    # Append to hash a hash of boolean keyword arguments
    _hash += generate_hash_of_string(",".join(rqtl_wrapper_bool_kwargs))

    # Temporarily substitute forward-slashes in hash with underscores
    _hash = _hash.replace("/", "_")

    _output_filename = f"{_hash}-output.csv"
    rqtl_wrapper_kwargs["filename"] = _output_filename

    return {
        "output_file": _output_filename,
        "rqtl_cmd": compose_rqtl_cmd(
            rqtl_wrapper_cmd=rqtl_wrapper_cmd,
            rqtl_wrapper_kwargs=rqtl_wrapper_kwargs,
            rqtl_wrapper_bool_kwargs=rqtl_wrapper_bool_kwargs,
        ),
    }


def process_rqtl_mapping(file_name: str) -> List:
    """Given an output file name, read in R/qtl results and return
    a List of marker objects"""
    marker_obs = []

    # Later I should probably redo this using csv.read to avoid the
    # awkwardness with removing quotes with [1:-1]
    outdir = os.path.join(get_tmpdir(),"gn3")

    with open( os.path.join(outdir,file_name),"r",encoding="utf-8") as the_file:
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
                "lod_score": float(line_items[3]),
            }
            marker_obs.append(this_marker)

    return marker_obs


def process_rqtl_pairscan(file_name: str, geno_file: str) -> List:
    """Given an output file name, read in R/qtl pair-scan results and return
    a list of both the JSON needed for the d3panels figure and a list of results
    to be used when generating the results table (which will include marker names)"""
    figure_data = pairscan_for_figure(file_name)
    table_data = pairscan_for_table(file_name, geno_file)

    return [figure_data, table_data]


def pairscan_for_figure(file_name: str) -> Dict:
    """Given an output file name, read in R/qtl pair-scan results and return
    the JSON needed for the d3panels figure"""
    figure_data = {}

    # Open the file with the actual results, written as a list of lists
    outdir = os.path.join(get_tmpdir(),"gn3")

    with open( os.path.join(outdir,file_name),"r",encoding="utf-8") as the_file:
        lod_results = []
        for i, line in enumerate(the_file):
            if i == 0:  # Skip first line
                continue
            line_items = [item.rstrip("\n") for item in line.split(",")]
            # Append all but first item in line
            lod_results.append(line_items[1:])
        figure_data["lod"] = lod_results

    # Open the map file with the list of markers/pseudomarkers and their
    # positions
    with open(
        os.path.join(
            current_app.config.get("TMPDIR", "/tmp"),
            "gn3",
            "MAP_" + file_name,
        ),
        "r",
        encoding="utf8",
    ) as the_file:
        chr_list = []  # type: List
        pos_list = []  # type: List
        for i, line in enumerate(the_file):
            if i == 0:  # Skip first line
                continue
            line_items = [item.rstrip("\n") for item in line.split(",")]
            chr_list.append(line_items[1][1:-1])
            pos_list.append(line_items[2])
        figure_data["chr"] = chr_list
        figure_data["pos"] = pos_list

    return figure_data


def get_marker_list(map_file: str) -> List:
    """
    Open the map file with the list of markers/pseudomarkers and create list of marker obs

    PARAMETERS:
    map_file: The map file output by R/qtl containing marker/pseudomarker positions
    """

    marker_list = []
    with open(
        os.path.join(
            current_app.config.get("TMPDIR", "/tmp"), "gn3", map_file
        ),
        "r",
        encoding="utf8",
    ) as map_fh:
        for line in map_fh.readlines()[1:]:
            line_items = [item.rstrip("\n") for item in line.split(",")]
            this_marker = {
                "name": line_items[0],
                "chr": line_items[1][
                    1:-1
                ],  # Strip quotes from beginning and end of chr string
                "pos": line_items[2],
            }

            marker_list.append(this_marker)

    return marker_list


def generate_table_rows(
    results_file: str, marker_list: List, original_markers: Dict
) -> List:
    """
    Open the file with the actual R/qtl pair-scan results and write them as
    they will be displayed in the results table

    PARAMETERS:
    results_file: The filename containing R/qtl pair-scan results
    marker_list: List of marker/pseudomarker names/positions from results
    original_markers: Dict of markers from the .geno file, for finding proximal/distal
                      markers to each pseudomarker
    """
    table_data = []
    with open(
        os.path.join(
            current_app.config.get("TMPDIR", "/tmp"), "gn3", results_file
        ),
        "r",
        encoding="utf8",
    ) as the_file:
        for i, line in enumerate(the_file.readlines()[1:]):
            marker_1 = marker_list[i]
            marker_1["proximal"], marker_1["distal"] = find_nearest_marker(
                marker_1["chr"], marker_1["pos"], original_markers
            )
            line_items = [item.rstrip("\n") for item in line.split(",")]
            for j, item in enumerate(line_items[1:]):
                marker_2 = marker_list[j]
                marker_2["proximal"], marker_2["distal"] = find_nearest_marker(
                    marker_2["chr"], marker_2["pos"], original_markers
                )
                try:
                    lod_score = f"{float(item):.3f}"
                except ValueError:
                    lod_score = f"{item}"

                table_data.append(
                    {
                        "proximal1": marker_1["proximal"],
                        "distal1": marker_1["distal"],
                        "pos1": f"Chr {marker_1['chr']} @ {float(marker_1['pos']):.1f} cM",
                        "lod": lod_score,
                        "proximal2": marker_2["proximal"],
                        "distal2": marker_2["distal"],
                        "pos2": f"Chr {marker_2['chr']} @ {float(marker_2['pos']):.1f} cM",
                    }
                )

    return table_data


def pairscan_for_table(file_name: str, geno_file: str) -> List:
    """
    Read in R/qtl pair-scan results and return as List representing
    table row contents

    PARAMETERS:
    file_name: The filename containing R/qtl pair-scan results
    geno_file: Filename of the genotype file (used to get marker positions)
    """

    # Open the map file with the list of markers/pseudomarkers and create list of marker obs
    marker_list = get_marker_list("MAP_" + file_name)

    # Get the list of original markers from the .geno file
    original_markers = build_marker_pos_dict(geno_file)

    # Open the file with the actual results and write the results as
    # they will be displayed in the results table
    table_data = generate_table_rows(file_name, marker_list, original_markers)

    return sorted(table_data, key=lambda i: float(i["lod"]), reverse=True)[:500]


def build_marker_pos_dict(genotype_file: str) -> Dict:
    """Gets list of markers and their positions from .geno file

    Basically a pared-down version of parse_genotype_file for R/qtl pair-scan"""

    with open(genotype_file, "r", encoding="utf8") as infile:
        contents = infile.readlines()

    # Get all lines after the metadata
    lines = tuple(
        line
        for line in contents
        if (
            (not line.strip().startswith("#"))
            and (not line.strip().startswith("@"))
            and (not line.strip() == "")
        )
    )

    header_items = lines[0].split("\t")
    mb_exists = "Mb" in header_items
    pos_column = (
        header_items.index("Mb") if mb_exists else header_items.index("cM")
    )

    the_markers = {"1": {}}  # type: Dict[str, Dict]
    for line in lines[1:]:  # The lines with markers
        line_items = line.split("\t")
        this_chr = line_items[0]
        if this_chr not in the_markers:
            the_markers[this_chr] = {}
        the_markers[this_chr][str(float(line_items[pos_column]))] = line_items[
            1
        ]

    return the_markers


def find_nearest_marker(
    the_chr: str, the_pos: str, marker_list: Dict
) -> Tuple[str, str]:
    """Given a chromosome and position of a pseudomarker (from R/qtl pair-scan results),
    return the nearest real marker"""

    pos_list = [float(pos) for pos in marker_list[the_chr]]

    # Get the position of the pseudomarker in the list of markers for the chr
    the_pos_index = bisect(pos_list, float(the_pos))

    proximal_marker = marker_list[the_chr][str(pos_list[the_pos_index - 1])]
    distal_marker = marker_list[the_chr][str(pos_list[the_pos_index])]

    return proximal_marker, distal_marker


def process_perm_output(file_name: str) -> Tuple[List, float, float]:
    """Given base filename, read in R/qtl permutation output and calculate
    suggestive and significant thresholds"""

    perm_results = []
    outdir = os.path.join(get_tmpdir(), "gn3")

    with open(os.path.join(outdir, file_name), "r", encoding="utf-8") as the_file:
        for i, line in enumerate(the_file):
            if i == 0:
                # Skip header line
                continue

            snp, chromosome, position, lod_score = line.split(",")
            perm_results.append(float(lod_score))

    suggestive = np.percentile(np.array(perm_results), 67)
    significant = np.percentile(np.array(perm_results), 95)

    return perm_results, suggestive, significant
