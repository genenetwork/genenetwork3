"""module contains code to preprocess and call wgcna script"""

import os
import json
import uuid
import subprocess
import base64

from gn3.settings import TMPDIR
from gn3.commands import run_cmd


def dump_wgcna_data(request_data: dict):
    """function to dump request data to json file"""
    filename = f"{str(uuid.uuid4())}.json"

    temp_file_path = os.path.join(TMPDIR, filename)

    request_data["TMPDIR"] = TMPDIR

    with open(temp_file_path, "w") as output_file:
        json.dump(request_data, output_file)

    return temp_file_path


def stream_cmd_output(socket, cmd: str):
    """function to stream in realtime"""
    # xtodo  syncing and closing /edge cases

    socket.emit("output", {"data", f"calling you script {cmd}"})

    results = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    for line in iter(results.stdout.readline, b""):
        line = line.decode("utf-8").rstrip()

        socket.emit("output",
                    {"data": line})
    # close above make sure  the process is closed

    socket.emit("output", {"data": "parsing the output results"})


def process_image(image_loc: str) -> bytes:
    """encode the image"""

    try:
        with open(image_loc, "rb") as image_file:
            return base64.b64encode(image_file.read())
    except FileNotFoundError as e:
        return b""


def compose_wgcna_cmd(rscript_path: str, temp_file_path: str):
    """function to componse wgcna cmd"""
    # (todo):issue relative paths to abs paths
    cmd = f"Rscript ./scripts/{rscript_path}  {temp_file_path}"
    return cmd


def call_wgcna_script(rscript_path: str, request_data: dict):
    """function to call wgcna script"""
    generated_file = dump_wgcna_data(request_data)
    cmd = compose_wgcna_cmd(rscript_path, generated_file)

    try:

        run_cmd_results = run_cmd(cmd)

        with open(generated_file, "r") as outputfile:

            output_file_data = json.load(outputfile)
            # json format only supports  unicode string// to get image data reconvert
            output_file_data["output"]["image_data"] = process_image(
                output_file_data["output"]["imageLoc"]).decode("ascii")

            if run_cmd_results["code"] != 0:
                return run_cmd_results
            return {
                "data": output_file_data,
                **run_cmd_results
            }
    except FileNotFoundError:
        # relook  at handling errors gn3
        return {
            "output": "output file not found"
        }
