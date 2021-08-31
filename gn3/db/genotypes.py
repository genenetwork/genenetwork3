"""Genotype utilities"""

import os
import gzip
from gn3.settings import GENOTYPE_FILES

def build_genotype_file(
        geno_name: str, base_dir: str = GENOTYPE_FILES,
        extension: str = "geno"):
    """Build the absolute path for the genotype file."""
    return "{}/{}.{}".format(os.path.abspath(base_dir), geno_name, extension)

def load_genotype_samples(genotype_filename: str, file_type: str = "geno"):
    """
    Load sample of strains from genotype files.

    DESCRIPTION:
    Traits can contain a varied number of strains, some of which do not exist in
    certain genotypes. In order to compute QTLs, GEMMAs, etc, we need to ensure
    to pick only those strains that exist in the genotype under consideration
    for the traits used in the computation.

    This function loads a list of samples from the genotype files for use in
    filtering out unusable strains.


    PARAMETERS:
    genotype_filename: The absolute path to the genotype file to load the
        samples from.
    file_type: The type of file. Currently supported values are 'geno' and
        'plink'.
    """
    file_type_fns = {
        "geno": __load_genotype_samples_from_geno,
        "plink": __load_genotype_samples_from_plink
    }
    return file_type_fns[file_type](genotype_filename)

def __load_genotype_samples_from_geno(genotype_filename: str):
    """
    Helper function for `load_genotype_samples` function.

    Loads samples from '.geno' files.
    """
    gzipped_filename = "{}.gz".format(genotype_filename)
    if os.path.isfile(gzipped_filename):
        genofile = gzip.open(gzipped_filename)
    else:
        genofile = open(genotype_filename)

    for row in genofile:
        line = row.strip()
        if (not line) or (line.startswith(("#", "@"))):
            continue
        break

    headers = line.split("\t")
    if headers[3] == "Mb":
        return headers[4:]
    return headers[3:]

def __load_genotype_samples_from_plink(genotype_filename: str):
    """
    Helper function for `load_genotype_samples` function.

    Loads samples from '.plink' files.
    """
    genofile = open(genotype_filename)
    return [line.split(" ")[1] for line in genofile]
