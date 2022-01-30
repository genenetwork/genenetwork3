"""module contains code to process ctl analysis data"""
import json
from gn3.commands import run_cmd

from gn3.computations.wgcna import dump_wgcna_data
from gn3.computations.wgcna import compose_wgcna_cmd
from gn3.computations.wgcna import process_image

from gn3.settings import TMPDIR


def call_ctl_script(data):
    """function to call ctl script"""
    data["imgDir"] = TMPDIR
    temp_file_name = dump_wgcna_data(data)
    cmd = compose_wgcna_cmd("ctl_analysis.R", temp_file_name)

    try:
        cmd_results = run_cmd(cmd)
        with open(temp_file_name, "r") as outputfile:
            if cmd_results["code"] != 0:
                return cmd_results

            output_file_data = json.load(outputfile)

            output_file_data["image_data"] = process_image(
                output_file_data["image_loc"]).decode("ascii")

            output_file_data["ctl_plots"] = [process_image(ctl_plot).decode("ascii") for
                                             ctl_plot in output_file_data["ctl_plots"]]

            return output_file_data

    except Exception as e:
        return str(e)
