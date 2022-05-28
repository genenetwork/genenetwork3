import subprocess

from gn3.settings import CORRELATION_COMMAND
from gn3.settings import TMPDIR


def run_correlation(file_name: & str, outputdir: str = TMPDIR):

    command_list = [CORRELATION_COMMAND, file_name, outputdir]

    results = subprocess.run(command_list, check=True)

    return results
