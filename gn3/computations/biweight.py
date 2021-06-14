

"""module contains script to call biweight mid\
correlation in R"""

import subprocess
from typing import List


def call_biweight_script(trait_vals: List,
                         target_vals: List,
                         path_to_script: str = "./biweight_R",
                         command: str = "Rscript"
                         ):
    '''biweight function'''
    args_1 = ' '.join(str(trait_val) for trait_val in trait_vals)
    args_2 = ' '.join(str(target_val) for target_val in target_vals)
    cmd = [command, path_to_script] + [args_1] + [args_2]

    results = subprocess.check_output(cmd, universal_newlines=True)

    return tuple([float(y) for y in results.split()])
