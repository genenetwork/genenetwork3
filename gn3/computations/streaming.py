"""Module contains streaming procedures  for genenetwork. """
import os
import subprocess
from functools import wraps
from flask import current_app, request


def read_file(file_path):
    """Add utility function to read files"""
    with open(file_path, "r", encoding="UTF-8") as file_handler:
        return file_handler.read()

def run_process(cmd, log_file, run_id):
    """Function to execute an external process and
       capture the stdout in a file
      input:
           cmd: the command to execute as a list of args.
           log_file: abs file path to write the stdout.
           run_id: unique id to identify the process

      output:
          Dict with the results for either success or failure.
    """
    try:
        # phase: execute the  rscript cmd
        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as process:
            for line in iter(process.stdout.readline, b""):
                # phase: capture the stdout for each line allowing read and write
                with open(log_file, "a+", encoding="utf-8") as file_handler:
                    file_handler.write(line.decode("utf-8"))
            process.wait()
            return {"msg": "success" if process.returncode == 0 else "Process failed",
                    "run_id": run_id,
                    "log" :  read_file(log_file),
                    "code": process.returncode}
    except subprocess.CalledProcessError as error:
        return {"msg": "error occurred",
                "code": error.returncode,
                "error": str(error),
                "run_id": run_id,
                "log" : read_file(log_file)}


def enable_streaming(func):
    """Decorator function to enable streaming for an endpoint
    Note: should only be used  in an app context
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        run_id = request.args.get("id")
        stream_output_file = os.path.join(current_app.config.get("TMPDIR"),
                                          f"{run_id}.txt")
        with open(stream_output_file, "w+", encoding="utf-8",
                  ) as file_handler:
            file_handler.write("File created for streaming\n"
                               )
        return func(stream_output_file, *args, **kwargs)
    return decorated_function
