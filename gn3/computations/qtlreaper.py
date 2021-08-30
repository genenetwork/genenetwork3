"""
This module contains functions to interact with the `qtlreaper` utility for
computation of QTLs.
"""
import os
import random
import string
import subprocess
from gn3.settings import TMPDIR, REAPER_COMMAND

def random_string(length):
    """Generate a random string of length `length`."""
    return "".join(
        random.choices(
            string.ascii_letters + string.digits, k=length))

def generate_traits_file(strains, trait_values, traits_filename):
    """
    Generate a traits file for use with `qtlreaper`.

    PARAMETERS:
    strains: A list of strains to use as the headers for the various columns.
    trait_values: A list of lists of values for each trait and strain.
    traits_filename: The tab-separated value to put the values in for
        computation of QTLs.
    """
    header = "Traits\t{}\n".format("\t".join(strains))
    data = [header] + [
        "T{}\t{}\n".format(i+1, "\t".join([str(i) for i in t]))
        for i, t in enumerate(trait_values[:-1])] + [
        "T{}\t{}".format(len(trait_values), "\t".join([str(i) for i in t]))
        for t in trait_values[-1:]]
    with open(traits_filename, "w") as outfile:
        outfile.writelines(data)

def create_output_directory(path: str):
    """Create the output directory at `path` if it does not exist."""
    try:
        os.mkdir(path)
    except OSError:
        pass

def run_reaper(
        genotype_filename: str, traits_filename: str,
        other_options: tuple = ("--n_permutations", 1000),
        separate_nperm_output: bool = False,
        output_dir: str = TMPDIR):
    """
    Run the QTLReaper command to compute the QTLs.

    PARAMETERS:
    genotype_filename: The complete path to a genotype file to use in the QTL
        computation.
    traits_filename: A path to a file previously generated with the
        `generate_traits_file` function in this module, to be used in the QTL
        computation.
    other_options: Other options to pass to the `qtlreaper` command to modify
        the QTL computations.
    separate_nperm_output: A flag indicating whether or not to provide a
        separate output for the permutations computation. The default is False,
        which means by default, no separate output file is created.
    output_dir: A path to the directory where the outputs are put

    RETURNS:
    The function returns a tuple of the main output file, and the output file
    for the permutation computations. If the `separate_nperm_output` is `False`,
    the second value in the tuple returned is `None`.

    RAISES:
    The function will raise a `subprocess.CalledProcessError` exception in case
    of any errors running the `qtlreaper` command.
    """
    create_output_directory(output_dir)
    output_filename = "{}/qtlreaper/main_output_{}.txt".format(
        output_dir, random_string(10))
    output_list = ["--main_output", output_filename]
    if separate_nperm_output:
        permu_output_filename = "{}/qtlreaper/permu_output_{}.txt".format(
            output_dir, random_string(10))
        output_list = output_list + ["--permu_output", permu_output_filename]
    else:
        permu_output_filename = None

    command_list = [
        REAPER_COMMAND, "--geno", genotype_filename,
        *other_options, # this splices the `other_options` list here
        "--traits", traits_filename, "--main_output", output_filename]

    subprocess.run(command_list, check=True)
    return (output_filename, permu_output_filename)
