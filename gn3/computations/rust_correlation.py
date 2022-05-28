import subprocess

from gn3.settings import CORRELATION_COMMAND
from gn3.settings import TMPDIR


def run_correlation(file_name: str, outputdir: str = TMPDIR):

    command_list = [CORRELATION_COMMAND, file_name, outputdir]

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
