"""module contains code to process ctl analysis data"""
import json
from gn3.commands import run_cmd

from gn3.computations.wgcna import dump_wgcna_data
from gn3.computations.wgcna import compose_wgcna_cmd


def call_ctl_script(data):
    """function to call ctl script"""

    temp_file_name = dump_wgcna_data(data)
    cmd = compose_wgcna_cmd("ctl_analysis.R", temp_file_name)

    try:
        cmd_results = run_cmd(cmd)
        print(cmd_results)
        with open(temp_file_name,"r") as outputfile:
            if cmd_results["code"] != 0:
                return cmd_results
            return json.load(outputfile)


    except Exception as e:
        return str(e)
