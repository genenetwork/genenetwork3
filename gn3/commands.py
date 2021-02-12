"""Procedures used to work with the various bio-informatics cli
commands"""
from typing import Dict
from typing import List
from typing import Optional

from gn3.file_utils import lookup_file
from gn3.file_utils import jsonfile_to_dict


# pylint: disable=locally-disabled, too-many-arguments
def compose_gemma_cmd(
        token: str,
        metadata_filename: str,
        gemma_wrapper_cmd: str = "gemma-wrapper",
        gemma_wrapper_kwargs: Optional[Dict] = None,
        gemma_kwargs: Optional[Dict] = None,
        gemma_args: Optional[List] = None) -> str:
    """Compose a valid GEMMA command given the correct values"""
    cmd = f"{gemma_wrapper_cmd} --json"
    if gemma_wrapper_kwargs:
        cmd += (" "  # Add extra space between commands
                " ".join([f" --{key} {val}" for key, val
                          in gemma_wrapper_kwargs.items()]))
    data = jsonfile_to_dict(lookup_file("TMPDIR",
                                        token,
                                        metadata_filename))
    geno_file = lookup_file(environ_var="TMPDIR",
                            root_dir="genotype",
                            file_name=data.get("geno", ""))
    pheno_file = lookup_file(environ_var="TMPDIR",
                             root_dir=token,
                             file_name=data.get("geno", ""))
    cmd += f" -- -g {geno_file} -p {pheno_file}"
    if gemma_kwargs:
        cmd += (" "
                " ".join([f" -{key} {val}"
                          for key, val in gemma_kwargs.items()]))
    if gemma_args:
        cmd += (" "
                " ".join([f" {arg}" for arg in gemma_args]))
    return cmd
