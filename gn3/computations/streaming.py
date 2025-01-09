"""Module contains streaming procedures  for genenetwork. """
import os
import subprocess
from functools import wraps
from flask import current_app, request


def run_process(cmd, output_file, run_id):
    """Function to execute an external process and
       capture the stdout in a file
      input:
           cmd: the command to execute as a list of args.
           output_file: abs file path to write the stdout.
           run_id: unique id to identify the process

      output:
          Dict with the results o either success or failure.
    """
    try:
        # phase: execute the  rscript cmd
        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as process:
            for line in iter(process.stdout.readline, b""):
                # phase: capture the stdout for eaching line allowing read and write
                with open(output_file, "a+", encoding="utf-8") as file_handler:
                    file_handler.write(line.decode("utf-8"))
            process.wait()
        if process.returncode == 0:
            return {"msg": "success", "code": 0, "run_id": run_id}
        return {"msg": "error occurred", "error": "Process failed",
                "code": process.returncode, "run_id": run_id}
    except subprocess.CalledProcessError as error:
        return {"msg": "error occurred",
                "error": str(error), "run_id": run_id}


def enable_streaming(func):
    """Decorator function to enable streaming for an endpoint
    Note: should be used only in an app context
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        run_id = request.args.get("id")
        stream_ouput_file = os.path.join(current_app.config.get("TMPDIR"),
                                         f"{run_id}.txt")
        with open(stream_ouput_file, "w+", encoding="utf-8",
                  ) as file_handler:
            file_handler.write("File created for streaming\n"
                               )
        return func(stream_ouput_file, *args, **kwargs)
    return decorated_function
