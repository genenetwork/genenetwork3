import os
import csv
import uuid
import json
from pathlib import Path
from typing import Dict

def generate_rqtl2_files(data, workspace_dir):
    """Prepare data  and generate necessary CSV  files
    required to write to control_file
    """
    # Map of file names to corresponding data keys in the provided dictionary
    file_to_name_map = {
        "geno_file": "geno_data",
        "pheno_file": "pheno_data",
        "geno_map_file": "geno_map_data",
        "pheno_map_file": "pheno_map_data",
        "phenocovar_file": "phenocovar_data",
    }
    parsed_files = {}
    for file_name, data_key in file_to_name_map.items():
        if data_key in data:
            file_path = write_to_csv(workspace_dir, f"{file_name}.csv", data[data_key])
            parsed_files[file_name] = file_path
    return {**data, **parsed_files}


def write_to_csv(work_dir, file_name, data:list[dict],
                      headers= None, delimiter=","):
    """Functions to write data list  to csv file
    if headers is not provided use the keys for first boject.
    """
    file_path = os.path.join(work_dir, file_name)
    if headers is None and data:
        headers = data[0].keys()
    with open(file_path, "w", encoding="utf-8") as file_handler:
        writer = csv.DictWriter(file_handler, fieldnames=headers,
                               delimiter=delimiter)
        writer.writeheader()
        for row in  data:
            writer.writerow(row)
        return file_path


def validate_required_keys(required_keys:list, data:dict) -> tuple[bool, str]:
    """Check for missing keys in data object"""
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        return False, f"Required key(s) missing: {', '.join(missing_keys)}"
    return True, ""


def compose_rqtl2_cmd(rqtl_path, input_file,
                      output_file, workspace_dir,
                      data, config):
    """Compose the command for running the R/QTL2 analysis."""
    # pylint: disable=R0913
    params = {
        "input_file": input_file,
        "directory": workspace_dir,
        "output_file": output_file,
        "nperm": data.get("nperm", 0),
        "threshold": data.get("threshold", 1),
        "cores": config.get('MULTIPROCESSOR_PROCS', 1)
    }
    rscript_path  = config.get("RSCRIPT", "Rscript")
    return  f"{rscript_path} { rqtl_path } " + " ".join(
        [f"--{key} {val}" for key, val in params.items()])
