import subprocess
import json
import os


from gn3.computations.qtlreaper import create_output_directory
from gn3.random import random_string
from gn3.settings import CORRELATION_COMMAND
from gn3.settings import TMPDIR


def generate_input_files(dataset: list[str], output_dir: str = TMPDIR):
    """function generates outputfiles and inputfiles"""

    tmp_dir = f"{output_dir}/correlation"

    create_output_directory(tmp_dir)

    tmp_file = os.path.join(tmp_dir, f"{random_string(10)}.txt")

    with open(tmp_file, "w") as file_writer:

        file_writer.write("\n".join(dataset))
    return (tmp_dir, tmp_file)


def generate_json_file(**kwargs):
    """generating json input file required by cargo"""

    (tmp_dir, tmp_file) = (kwargs.get("tmp_dir"), kwargs.get("tmp_file"))

    tmp_json_file = os.path.join(tmp_dir, f"{random_string(10)}.json")

    correlation_args = {
        "method": kwargs.get("method", "pearson"),
        "file_path": tmp_file,
        "x_vals": kwargs.get("x_vals"),
        "file_delimiter": kwargs.get("delimiter", ",")
    }

    with open(tmp_json_file, "w") as outputfile:
        json.dump(correlation_args, outputfile)

    return tmp_json_file


def run_correlation(dataset, trait_vals: list[str], method: str, delimiter: str):
    """entry function to call rust correlation"""

    json_file = generate_json_file(**
                                   {"method": method, "delimiter": delimiter, "x_vals": trait_vals})

    command_list = [CORRELATION_COMMAND, json_file, outputdir]

    results = subprocess.run(command_list, check=True)

    return results


def parse_correlation_output(result_file: str):

    corr_results = []

    with open(result_file, "r") as file_reader:

        for line in file_reader:

            (trait_name, corr_coeff, p_val) = line.rstrip().split(",")
            corr_data = {
                "trait_name": trait_name,
                "corr_coeff": corr_coeff,
                "p_val": p_val
            }

            corr_results.append(corr_data)

    return corr_results
