"""Module contains functions to parse and process rqtl2 input and output"""
import os
import csv
import uuid
import json
from pathlib import Path
from typing import List
from typing import Dict
from typing import Any

def generate_rqtl2_files(data, workspace_dir):
    """Prepare data  and generate necessary CSV  files
    required to write to control_file
    """
    file_to_name_map = {
        "geno_file": "geno_data",
        "pheno_file": "pheno_data",
        "geno_map_file": "geno_map_data",
        "physical_map_file": "physical_map_data",
        "phenocovar_file": "phenocovar_data",
    }
    parsed_files = {}
    for file_name, data_key in file_to_name_map.items():
        if data_key in data:
            file_path = write_to_csv(
                workspace_dir, f"{file_name}.csv", data[data_key])
            if file_path:
                parsed_files[file_name] = file_path
    return {**data, **parsed_files}


def write_to_csv(work_dir, file_name, data: list[dict],
                 headers=None, delimiter=","):
    """Functions to write data list  to csv file
    if headers is not provided use the keys for first boject.
    """
    if not data:
        return ""
    if headers is None:
        headers = data[0].keys()
    file_path = os.path.join(work_dir, file_name)
    with open(file_path, "w", encoding="utf-8") as file_handler:
        writer = csv.DictWriter(file_handler, fieldnames=headers,
                                delimiter=delimiter)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
        # return the relative file to the workspace see rqtl2 docs
        return file_name


def validate_required_keys(required_keys: list, data: dict) -> tuple[bool, str]:
    """Check for missing keys in data object"""
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        return False, f"Required key(s) missing: {', '.join(missing_keys)}"
    return True, ""


def compose_rqtl2_cmd(# pylint: disable=[too-many-positional-arguments]
        rqtl_path, input_file, output_file, workspace_dir, data, config):
    """Compose the command for running the R/QTL2 analysis."""
    # pylint: disable=R0913
    params = {
        "input_file": input_file,
        "directory": workspace_dir,
        "output_file": output_file,
        "nperm": data.get("nperm", 0),
        "method": data.get("method", "HK"),
        "threshold": data.get("threshold", 1),
        "cores": config.get('MULTIPROCESSOR_PROCS', 1)
    }
    rscript_path = config.get("RSCRIPT", os.environ.get("RSCRIPT", "Rscript"))
    return f"{rscript_path} { rqtl_path } " + " ".join(
        [f"--{key} {val}" for key, val in params.items()])


def create_file(file_path):
    """Utility function to create file given a file_path"""
    try:
        with open(file_path, "x", encoding="utf-8") as _file_handler:
            return True, f"File created at {file_path}"
    except FileExistsError:
        return False, "File Already Exists"


def prepare_files(tmpdir):
    """Prepare necessary files and workspace dir  for computation."""
    workspace_dir = os.path.join(tmpdir, str(uuid.uuid4()))
    Path(workspace_dir).mkdir(parents=False, exist_ok=True)
    input_file = os.path.join(
        workspace_dir, f"rqtl2-input-{uuid.uuid4()}.json")
    output_file = os.path.join(
        workspace_dir, f"rqtl2-output-{uuid.uuid4()}.json")

    # to ensure streaming api has access to file  even after computation ends
    # .. Create the log file outside the workspace_dir
    log_file = os.path.join(tmpdir, f"rqtl2-log-{uuid.uuid4()}")
    for file_path in [input_file, output_file, log_file]:
        create_file(file_path)
    return workspace_dir, input_file, output_file, log_file


def write_input_file(input_file, workspace_dir, data):
    """
    Write input data to a json file to be passed
    as input to the rqtl2 script
    """
    with open(input_file, "w+", encoding="UTF-8") as file_handler:
        # todo choose a better variable name
        rqtl2_files = generate_rqtl2_files(data, workspace_dir)
        json.dump(rqtl2_files, file_handler)


def read_output_file(output_path: str) -> dict:
    """function to read output file json generated from rqtl2
    see rqtl2_wrapper.R script for the expected output
    """
    with open(output_path, "r", encoding="utf-8") as file_handler:
        results = json.load(file_handler)
        return results


def process_permutation(data):
    """ This function processses output data from the output results.
    input: data object  extracted from the output_file
    returns:
        dict: A dict containing
            * phenotypes array
            * permutations as dict with keys as permutation_id
            * significance_results with keys as threshold values
    """

    perm_file = data.get("permutation_file")
    with open(perm_file, "r", encoding="utf-8") as file_handler:
        reader = csv.reader(file_handler)
        phenotypes = next(reader)[1:]
        perm_results = {_id: float(val) for _id, val, *_ in reader}
        _, significance = fetch_significance_results(data.get("significance_file"))
        return {
        "phenotypes": phenotypes,
        "perm_results": perm_results,
        "significance": significance,
    }


def fetch_significance_results(file_path: str):
    """
    Processes the 'significance_file' from the given data object to extract
    phenotypes and significance values.
    thresholds  values are: (0.05, 0.01)
    Args:
        file_path (str): file_Path for the significance output

    Returns:
        tuple: A tuple containing
            *  phenotypes (list): List of phenotypes
            *  significances (dict): A dictionary where keys
               ...are threshold values and values are lists
               of significant results corresponding to each threshold.
    """
    with open(file_path, "r", encoding="utf-8") as file_handler:
        reader = csv.reader(file_handler)
        results = {}
        phenotypes = next(reader)[1:]
        for line in reader:
            threshold, significance = line[0], line[1:]
            results[threshold] = significance
        return (phenotypes, results)


def process_scan_results(qtl_file_path: str, map_file_path: str) -> List[Dict[str, Any]]:
    """Function to process genome scanning results and obtain marker_name, Lod score,
    marker_position, and chromosome.
    Args:
        qtl_file_path (str): Path to the QTL scan results CSV file.
        map_file_path (str): Path to the map file from the script.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing the marker data.
    """
    map_data = {}
    # read the genetic map
    with open(map_file_path, "r", encoding="utf-8") as file_handler:
        reader = csv.reader(file_handler)
        next(reader)
        for line in reader:
            marker, chr_, cm_, mb_ = line
            cm: float | None = float(cm_) if cm_ and cm_ != "NA" else None
            mb: float | None = float(mb_) if mb_ and mb_ != "NA" else None
            map_data[marker] = {"chr": chr_, "cM": cm, "Mb": mb}

    # Process QTL scan results and merge the positional data
    results = []
    with open(qtl_file_path, "r", encoding="utf-8") as file_handler:
        reader = csv.reader(file_handler)
        next(reader)
        for line in reader:
            marker = line[0]
            lod_score = line[1]
            results.append({
                "name": marker,
                "lod_score": float(lod_score),
                **map_data.get(marker, {})  # Add chromosome and positions if available
            })
    return results


def process_qtl2_results(output_file: str) -> Dict[str, Any]:
    """Function provides abstraction for processing all QTL2 mapping results.

    Args: * File path to to the output generated

    Returns:
        Dict[str, any]: A dictionary containing both QTL
            and permutation results along with input data.
    """
    results  = read_output_file(output_file)
    qtl_results = process_scan_results(results["scan_file"],
                                       results["map_file"])
    permutation_results = process_permutation(results) if results["permutations"] > 0 else {}
    return {
        **results,
        "qtl_results": qtl_results,
        "permutation_results": permutation_results
    }
