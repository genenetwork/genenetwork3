"""
This module contains functions to interact with the `qtlreaper` utility for
computation of QTLs.
"""
import os
import subprocess
from typing import Union

from gn3.random import random_string
from gn3.settings import TMPDIR, REAPER_COMMAND

def generate_traits_file(strains, trait_values, traits_filename):
    """
    Generate a traits file for use with `qtlreaper`.

    PARAMETERS:
    strains: A list of strains to use as the headers for the various columns.
    trait_values: A list of lists of values for each trait and strain.
    traits_filename: The tab-separated value to put the values in for
        computation of QTLs.
    """
    header = "Trait\t{}\n".format("\t".join(strains))
    data = (
        [header] +
        ["{}\t{}\n".format(i+1, "\t".join([str(i) for i in t]))
         for i, t in enumerate(trait_values[:-1])] +
        ["{}\t{}".format(
            len(trait_values), "\t".join([str(i) for i in t]))
         for t in trait_values[-1:]])
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
        other_options: tuple = ("--n_permutations", "1000"),
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
    create_output_directory("{}/qtlreaper".format(output_dir))
    output_filename = "{}/qtlreaper/main_output_{}.txt".format(
        output_dir, random_string(10))
    output_list = ["--main_output", output_filename]
    if separate_nperm_output:
        permu_output_filename: Union[None, str] = "{}/qtlreaper/permu_output_{}.txt".format(
            output_dir, random_string(10))
        output_list = output_list + [
            "--permu_output", permu_output_filename] # type: ignore[list-item]
    else:
        permu_output_filename = None

    command_list = [
        REAPER_COMMAND, "--geno", genotype_filename,
        *other_options, # this splices the `other_options` list here
        "--traits", traits_filename,
        *output_list # this splices the `output_list` list here
    ]

    subprocess.run(command_list, check=True)
    return (output_filename, permu_output_filename)

def chromosome_sorter_key_fn(val):
    """
    Useful for sorting the chromosomes
    """
    if isinstance(val, int):
        return val
    return ord(val)

def organise_reaper_main_results(parsed_results):
    """
    Provide the results of running reaper in a format that is easier to use.
    """
    def __organise_by_chromosome(chr_name, items):
        chr_items = [item for item in items if item["Chr"] == chr_name]
        return {
            "Chr": chr_name,
            "loci": [{
                "Locus": locus["Locus"],
                "cM": locus["cM"],
                "Mb": locus["Mb"],
                "LRS": locus["LRS"],
                "Additive": locus["Additive"],
                "pValue": locus["pValue"]
            } for locus in chr_items]}

    def __organise_by_id(identifier, items):
        id_items = [item for item in items if item["ID"] == identifier]
        unique_chromosomes = {item["Chr"] for item in id_items}
        return {
            "ID": identifier,
            "chromosomes": {
                _chr["Chr"]: _chr for _chr in [
                    __organise_by_chromosome(chromo, id_items)
                    for chromo in sorted(
                        unique_chromosomes, key=chromosome_sorter_key_fn)]}}

    unique_ids = {res["ID"] for res in parsed_results}
    return {
        trait["ID"]: trait for trait in
        [__organise_by_id(_id, parsed_results) for _id in sorted(unique_ids)]}

def parse_reaper_main_results(results_file):
    """
    Parse the results file of running QTLReaper into a list of dicts.
    """
    with open(results_file, "r") as infile:
        lines = infile.readlines()

    def __parse_column_float_value(value):
        # pylint: disable=W0702
        try:
            return float(value)
        except:
            return value

    def __parse_column_int_value(value):
        # pylint: disable=W0702
        try:
            return int(value)
        except:
            return value

    def __parse_line(line):
        items = line.strip().split("\t")
        return items[0:2] + [__parse_column_int_value(items[2])] + [
            __parse_column_float_value(item) for item in items[3:]]

    header = lines[0].strip().split("\t")
    return [dict(zip(header, __parse_line(line))) for line in lines[1:]]

def parse_reaper_permutation_results(results_file):
    """
    Parse the results QTLReaper permutations into a list of values.
    """
    with open(results_file, "r") as infile:
        lines = infile.readlines()

    return [float(line.strip()) for line in lines]
