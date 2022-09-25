"""module contains code to preprocess and call wgcna script"""

import os
import json
import uuid
import subprocess
import base64


from gn3.settings import TMPDIR
from gn3.settings import R_SCRIPTS
from gn3.commands import run_cmd


def dump_wgcna_data(request_data: dict):
    """function to dump request data to json file"""
    filename = f"{str(uuid.uuid4())}.json"

    temp_file_path = os.path.join(TMPDIR, filename)

    request_data["TMPDIR"] = TMPDIR

    with open(temp_file_path, "w", encoding="utf-8") as output_file:
        json.dump(request_data, output_file)

    return temp_file_path


def stream_cmd_output(socketio, request_data, cmd: str):
    """function to stream in realtime"""
    # xtodo  syncing and closing /edge cases

    socketio.emit("output", {"data": f"calling you script {cmd}"},
                  namespace="/", room=request_data["socket_id"])
    with subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True) as results:
        if results.stdout is not None:
            for line in iter(results.stdout.readline, b""):
                socketio.emit("output",
                              {"data": line.decode("utf-8").rstrip()},
                              namespace="/", room=request_data["socket_id"])

                socketio.emit(
                    "output", {"data":
                               "parsing the output results"}, namespace="/",
                    room=request_data["socket_id"])


def process_image(image_loc: str) -> bytes:
    """encode the image"""

    try:
        with open(image_loc, "rb") as image_file:
            return base64.b64encode(image_file.read())
    except FileNotFoundError:
        return b""


def compose_rscript_cmd(script_path: str,
                        file_name: str,
                        temp_file_path: str):

    cmd = f'"Rscript {os.path.join(script_path,file_name)}  {temp_file_path}"'
    return cmd


def call_wgcna_script(rscript_path: str, request_data: dict):
    """function to call wgcna script"""
    generated_file = dump_wgcna_data(request_data)

    cmd = compose_rscript_cmd(rscript_path, generated_file)

    # stream_cmd_output(request_data, cmd)  disable streaming of data

    try:

        run_cmd_results = run_cmd(cmd)

        with open(generated_file, "r", encoding="utf-8") as outputfile:

            if run_cmd_results["code"] != 0:
                return run_cmd_results

            output_file_data = json.load(outputfile)
            output_file_data["output"]["image_data"] = process_image(
                output_file_data["output"]["imageLoc"]).decode("ascii")
            # json format only supports  unicode string// to get image data reconvert

            return {
                "data": output_file_data,
                **run_cmd_results
            }
    except FileNotFoundError:
        # relook  at handling errors gn3
        return {
            "output": "output file not found"
        }
