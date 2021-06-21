"""module contains script to call biweight midcorrelation in R"""
import subprocess

from typing import List
from typing import Tuple

from gn3.settings import BIWEIGHT_RSCRIPT


def calculate_biweight_corr(trait_vals: List,
                            target_vals: List,
                            path_to_script: str = BIWEIGHT_RSCRIPT,
                            command: str = "Rscript"
                            ) -> Tuple[float, float]:
    """biweight function"""

    args_1 = ' '.join(str(trait_val) for trait_val in trait_vals)
    args_2 = ' '.join(str(target_val) for target_val in target_vals)
    cmd = [command, path_to_script] + [args_1] + [args_2]

    results = subprocess.check_output(cmd, universal_newlines=True)

    (corr_coeff, p_val) = tuple([float(y) for y in results.split()])

    return (corr_coeff, p_val)
