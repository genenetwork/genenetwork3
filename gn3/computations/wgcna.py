"""module contains code to preprocess and call wgcna script"""

import os
import json
import uuid
from gn3.settings import TMPDIR

from gn3.commands import run_cmd


def dump_wgcna_data(request_data: dict):
    """function to dump request data to json file"""
    filename = f"{str(uuid.uuid4())}.json"

    temp_file_path = os.path.join(TMPDIR, filename)

    with open(temp_file_path, "w") as output_file:
        json.dump(request_data, output_file)

    return temp_file_path


def compose_wgcna_cmd(rscript_path: str, temp_file_path: str):
    """function to componse wgcna cmd"""
    cmd = f"Rscript {rscript_path}  {temp_file_path}"
    return cmd


def call_wgcna_script(rscript_path: str, request_data: dict):
    """function to call wgcna script"""
    generated_file = dump_wgcna_data(request_data)
    cmd = compose_wgcna_cmd(rscript_path, generated_file)

    try:
        return run_cmd(cmd)
    except Exception as error:
        raise error
