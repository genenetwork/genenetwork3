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


def generate_json_file(tmp_dir, tmp_file, method, delimiter, x_vals) -> str:
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
                    list[str],
                    method: str,
                    delimiter: str):
    """entry function to call rust correlation"""

    (tmp_dir, tmp_file) = generate_input_files(dataset)

    (output_file, json_file) = generate_json_file(tmp_dir=tmp_dir,
                                                  tmp_file=tmp_file,
                                                  method=method,
                                                  delimiter=delimiter,
                                                  x_vals=trait_vals)

    command_list = [CORRELATION_COMMAND, json_file, TMPDIR]

    rls = subprocess.run(command_list, check=True)

    rs = parse_correlation_output(output_file,10000)

    return rs


def parse_correlation_output(result_file: str, top_n: int = 500) -> list[dict]:
    """parse file output """

    corr_results = []

    with open(result_file, "r", encoding="utf-8") as file_reader:

        lines = [next(file_reader) for x in range(top_n)]

        for line in lines:

            (trait_name, corr_coeff, p_val) = line.rstrip().split(",")
            corr_data = {
                "num_overlap": 00,  # to be later fixed
                "corr_coefficient": corr_coeff,
                "p_value": p_val
            }

            corr_results.append({trait_name: corr_data})

    return corr_results




# computation specific;sample_r,lit_corr
def compute_top_n(first_run_results,init_type,dataset_1,dataset_2,dataset_type:str):
    if dataset__type.lower()!= "probeset":
        return first_run_results

    if  init_type == "sample":
        # do both lit and tissue

        results_a = run_correlation(dataset_1, x_vals_1,method,delimiter)

        results_b = lit_correlation_for_trait(unkown)


        # question how do we merge this





    if  init_type == "tissue":
        # do sample and tissue


        file_a  =  run_correlation(dataset_1,x_vals_1,method,delimiter)

        result_b = lit_correlation_for_trait(unkown)

        # merge the results



    if  init_type == "lit":

        file_a  = run_correlation()

        file_b = run_correlation()

        join <(file_a) <(file_b)

    # do the merge here
        # do both  sample and tissue





