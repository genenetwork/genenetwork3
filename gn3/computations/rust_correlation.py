"""module contains code integration  correlation implemented in rust here

https://github.com/Alexanderlacuna/correlation_rust

"""

import subprocess
import json
import os

from gn3.computations.qtlreaper import create_output_directory
from gn3.random import random_string
from gn3.settings import CORRELATION_COMMAND
from gn3.settings import TMPDIR


def generate_input_files(dataset: list[str],
                         output_dir: str = TMPDIR) -> tuple[str, str]:
    """function generates outputfiles and inputfiles"""

    tmp_dir = f"{output_dir}/correlation"

    create_output_directory(tmp_dir)

    tmp_file = os.path.join(tmp_dir, f"{random_string(10)}.txt")

    with open(tmp_file, "w", encoding="utf-8") as file_writer:

        file_writer.write("\n".join(dataset))
    return (tmp_dir, tmp_file)


def generate_json_file(tmp_dir, tmp_file,
                       method, delimiter, x_vals) -> tuple[str, str]:
    """generating json input file required by cargo"""

    tmp_json_file = os.path.join(tmp_dir, f"{random_string(10)}.json")

    output_file = os.path.join(tmp_dir, f"{random_string(10)}.txt")

    correlation_args = {
        "method": method,
        "file_path": tmp_file,
        "x_vals": x_vals,
        "sample_values": "bxd1",
        "output_file": output_file,
        "file_delimiter": delimiter
    }

    with open(tmp_json_file, "w", encoding="utf-8") as outputfile:
        json.dump(correlation_args, outputfile)

    return (output_file, tmp_json_file)


def run_correlation(dataset, trait_vals:
                    str,
                    method: str,
                    delimiter: str,
                    corr_type: str = "sample",
                    top_n: int = 500):
    """entry function to call rust correlation"""

    (tmp_dir, tmp_file) = generate_input_files(dataset)

    (output_file, json_file) = generate_json_file(tmp_dir=tmp_dir,
                                                  tmp_file=tmp_file,
                                                  method=method,
                                                  delimiter=delimiter,
                                                  x_vals=trait_vals)

    command_list = [CORRELATION_COMMAND, json_file, TMPDIR]

    subprocess.run(command_list, check=True)

    results = parse_correlation_output(output_file, corr_type, top_n)

    return results


def parse_correlation_output(result_file: str,
                             corr_type: str, top_n: int = 500) -> dict:
    """parse file output """

    corr_results = {}

    with open(result_file, "r", encoding="utf-8") as file_reader:

        lines = [next(file_reader) for x in range(top_n)]

        for line in lines:
            (trait_name, corr_coeff,
                p_val, num_overlap) = line.rstrip().split(",")

            if corr_type == "sample":

                corr_data = {
                    "num_overlap": num_overlap,
                    "corr_coefficient": corr_coeff,
                    "p_value": p_val
                }

            if corr_type == "tissue":
                corr_data = {
                    "tissue_corr": corr_coeff,
                    "tissue_number": num_overlap,
                    "tissue_p_val": p_val
                }

            corr_results[trait_name] = corr_data

    return corr_results


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
                         all_samples: dict[str, str],
                         dataset_samples: list[str]) -> dict[str, str]:
    """dependeing on the sample_type fetch the correct sample data """

    if sample_type == "samples_primary":

        data = get_samples(all_samples=all_samples,
                           base_samples=dataset_samples, excluded=[])

    elif sample_type == "samples_other":
        data = get_samples(
            all_samples=all_samples,
            base_samples=[],
            excluded=dataset_samples)
    else:
        data = get_samples(
            all_samples=all_samples, base_samples=[], excluded=[])
    return data


def parse_tissue_corr_data(symbol_name: str,
                           symbol_dict: dict,
                           dataset_symbols: dict,
                           dataset_vals: dict):
    """parset tissue data input"""

    results = None

    if symbol_name and symbol_name.lower() in symbol_dict:
        x_vals = ",".join([str(val)
                           for val in symbol_dict[symbol_name.lower()]])

        data = []

        for (trait, symbol) in dataset_symbols.items():
            try:
                corr_vals = dataset_vals.get(symbol.lower())

                if corr_vals:
                    corr_vals = [str(trait)] + corr_vals

                    data.append(",".join([str(x) for x in corr_vals]))

            except AttributeError:
                pass

        results = (x_vals, data)

    return results


def parse_lit_corr_data(_trait, _dataset):
    """todo:parse lit data"""


def merge_corr_results(results_a: dict, results_b: dict):
    """merge results when computing all correlations"""

    results = []

    for (name, corr_values) in results_a.items():
        if results_b.get(name):
            tmp = results_a[name]  #dict
            tmp.update(results_b[name])  

            output = tmp
        else:
            output = corr_values

        results.append({name: output})
    return results
