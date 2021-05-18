"""Procedures related rqtl computations"""

from typing import Dict
from gn3.commands import compose_rqtl_cmd
from gn3.computations.gemma import generate_hash_of_string
from gn3.fs_helpers import get_hash_of_files

def generate_rqtl_cmd(rqtl_wrapper_cmd: str,
                      rqtl_wrapper_kwargs: Dict,
                      rqtl_wrapper_bool_kwargs: list) -> Dict:
    """Given the base rqtl_wrapper command and
dict of keyword arguments, return the full rqtl_wrapper command and an
output filename generated from a hash of the genotype and phenotype files

    """

    # Generate a hash from contents of the genotype and phenotype files
    _hash = get_hash_of_files(
        [v for k, v in rqtl_wrapper_kwargs.items() if k in ["g", "p"]])

    # Append to hash a hash of keyword arguments
    _hash += generate_hash_of_string(
        ",".join([f"{k}:{v}" for k, v in rqtl_wrapper_kwargs.items() if k not in ["g", "p"]]))

    # Append to hash a hash of boolean keyword arguments
    _hash += generate_hash_of_string(
        ",".join(rqtl_wrapper_bool_kwargs))

    _output_filename = f"{_hash}-output.json"
    return {
        "output_file":
        _output_filename,
        "rqtl_cmd":
        compose_rqtl_cmd(rqtl_wrapper_cmd=rqtl_wrapper_cmd,
                         rqtl_wrapper_kwargs=rqtl_wrapper_kwargs,
                         rqtl_wrapper_bool_kwargs=rqtl_wrapper_bool_kwargs)
    }
