"""Procedures related rqtl computations"""

from typing import Dict
from gn3.commands import compose_rqtl_cmd
from gn3.fs_helpers import get_hash_of_files

def generate_rqtl_cmd(rqtl_wrapper_cmd: str,
                      rqtl_wrapper_kwargs: Dict) -> Dict:
    """Given the base rqtl_wrapper command and
dict of keyword arguments, return the full rqtl_wrapper command and an
output filename generated from a hash of the genotype and phenotype files

    """

    _hash = get_hash_of_files(
        [v for k, v in rqtl_wrapper_kwargs.items() if k in ["g", "p"]])

    _output_filename = f"{_hash}-output.json"
    return {
        "output_file":
        _output_filename,
        "rqtl_cmd":
        compose_rqtl_cmd(rqtl_wrapper_cmd=rqtl_wrapper_cmd,
                         rqtl_wrapper_kwargs=rqtl_wrapper_kwargs)
    }
