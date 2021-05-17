"""Procedures related rqtl computations"""
import os

from typing import Dict
from gn3.commands import compose_rqtl_cmd
from gn3.fs_helpers import get_hash_of_files

def generate_rqtl_cmd(rqtl_wrapper_cmd: str,
                      output_dir: str,
                      rqtl_wrapper_kwargs: Dict) -> Dict:

    _hash = get_hash_of_files(
        [v for k, v in rqtl_wrapper_kwargs.items() if k in ["g", "p", "addcovar",
                                                    "model", "method",
                                                    "interval", "nperm",
                                                    "scale", "control"]])

    _output_filename = f"{_hash}-output.json"
    return {
        "output_file":
        _output_filename,
        "rqtl_cmd":
        compose_rqtl_cmd(rqtl_wrapper_cmd=rqtl_wrapper_cmd,
                         rqtl_wrapper_kwargs=rqtl_wrapper_kwargs)
    }