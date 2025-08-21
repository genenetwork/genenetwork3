"""module contains code integration  correlation implemented in rust here

https://github.com/Alexanderlacuna/correlation_rust

"""
import os
import csv
import json
import traceback
import subprocess

from flask import current_app

from gn3.computations.qtlreaper import create_output_directory
from gn3.chancy import random_string
from gn3.settings import TMPDIR


def generate_input_files(dataset: list[str],
                         output_dir: str = TMPDIR) -> tuple[str, str]:
    """function generates outputfiles and inputfiles"""
    tmp_dir = f"{output_dir}/correlation"
    create_output_directory(tmp_dir)
    tmp_file = os.path.join(tmp_dir, f"{random_string(10)}.txt")
    with open(tmp_file, "w", encoding="utf-8") as op_file:
        writer = csv.writer(
            op_file, delimiter=",", dialect="unix",
            quoting=csv.QUOTE_NONE, escapechar="\\")
        writer.writerows(dataset)

    return (tmp_dir, tmp_file)


def generate_json_file(
        tmp_dir, tmp_file, method, delimiter, x_vals) -> tuple[str, str]:
    """generating json input file required by cargo"""
    tmp_json_file = os.path.join(tmp_dir, f"{random_string(10)}.json")
    output_file = os.path.join(tmp_dir, f"{random_string(10)}.txt")

    with open(tmp_json_file, "w", encoding="utf-8") as outputfile:
        json.dump({
            "method": method,
            "file_path": tmp_file,
            "x_vals": x_vals,
            "sample_values": "bxd1",
            "output_file": output_file,
            "file_delimiter": delimiter
        }, outputfile)
    return (output_file, tmp_json_file)


def run_correlation(
        dataset, trait_vals: str, method: str, delimiter: str,
        corr_type: str = "sample"):
    """entry function to call rust correlation"""

    # pylint: disable=[too-many-arguments, too-many-positional-arguments]
    correlation_command = current_app.config["CORRELATION_COMMAND"] # make arg?
    (tmp_dir, tmp_file) = generate_input_files(dataset)
    (output_file, json_file) = generate_json_file(
        tmp_dir=tmp_dir, tmp_file=tmp_file, method=method, delimiter=delimiter,
        x_vals=trait_vals)
    command_list = [correlation_command, json_file, TMPDIR]
    try:
        subprocess.run(command_list, check=True, capture_output=True)
    except subprocess.CalledProcessError as cpe:
        actual_command = (
            os.readlink(correlation_command)
            if os.path.islink(correlation_command)
            else correlation_command)
        raise Exception(# pylint: disable=[broad-exception-raised]
            command_list,
            actual_command,
            cpe.stdout,
            traceback.format_exc().split()
        ) from cpe

    return parse_correlation_output(output_file, corr_type)


def parse_correlation_output(result_file: str, corr_type: str) -> dict:
    """parse file output """
    # current types are sample and tissue
    def __parse_line__(line):
        (trait_name, corr_coeff, p_val, num_overlap) = line.rstrip().split(",")
        if corr_type == "sample":
            return (trait_name, {
                "num_overlap": num_overlap,
                "corr_coefficient": corr_coeff,
                "p_value": p_val
            })

        if corr_type == "tissue":
            return (
                trait_name,
                {
                    "tissue_corr": corr_coeff,
                    "tissue_number": num_overlap,
                    "tissue_p_val": p_val
                })

        return tuple(trait_name, {})

    with open(result_file, "r", encoding="utf-8") as file_reader:
        return dict([__parse_line__(line) for line in file_reader])

    return {}


def get_samples(all_samples: dict[str, str],
                base_samples: list[str],
                excluded: list[str]):
    """filter null samples and excluded samples"""

    data = {}

    if base_samples:
        fls = [
            sm for sm in base_samples if sm not in excluded]
        for sample in fls:
            if sample in all_samples:
                smp_val = all_samples[sample].strip()
                if smp_val.lower() != "x":
                    data[sample] = float(smp_val)

        return data

    return({key: float(val.strip()) for (key, val) in all_samples.items()
            if key not in excluded and val.lower().strip() != "x"})


def get_sample_corr_data(sample_type: str,
                         sample_data: dict[str, str],
                         dataset_samples: list[str]) -> dict[str, str]:
    """dependeing on the sample_type fetch the correct sample data """

    if sample_type == "samples_primary":

        data = get_samples(all_samples=sample_data,
                           base_samples=dataset_samples, excluded=[])

    elif sample_type == "samples_other":
        data = get_samples(
            all_samples=sample_data,
            base_samples=[],
            excluded=dataset_samples)
    else:
        data = get_samples(
            all_samples=sample_data, base_samples=[], excluded=[])
    return data


def parse_tissue_corr_data(symbol_name: str,
                           symbol_dict: dict,
                           dataset_symbols: dict,
                           dataset_vals: dict):
    """parset tissue data input"""

    results = None

    if symbol_name and symbol_name.lower() in symbol_dict:
        x_vals = [float(val) for val in symbol_dict[symbol_name.lower()]]

        data = []

        for (trait, symbol) in dataset_symbols.items():
            try:
                corr_vals = dataset_vals.get(symbol.lower())

                if corr_vals:
                    data.append([str(trait)] + corr_vals)

            except AttributeError:
                pass

        results = (x_vals, data)

    return results
