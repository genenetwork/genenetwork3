"""Procedures used to work with the various bio-informatics cli
commands"""
import subprocess

from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional
from uuid import uuid4
from redis.client import Redis  # Used only in type hinting

from gn3.exceptions import RedisConnectionError
from gn3.file_utils import lookup_file
from gn3.file_utils import jsonfile_to_dict


# pylint: disable=locally-disabled, too-many-arguments
def compose_gemma_cmd(
        token: str,
        metadata_filename: str,
        gemma_wrapper_cmd: str = "gemma-wrapper",
        gemma_wrapper_kwargs: Optional[Dict] = None,
        gemma_kwargs: Optional[Dict] = None,
        gemma_args: Optional[List] = None) -> str:
    """Compose a valid GEMMA command given the correct values"""
    cmd = f"{gemma_wrapper_cmd} --json"
    if gemma_wrapper_kwargs:
        cmd += (" "  # Add extra space between commands
                " ".join([f" --{key} {val}" for key, val
                          in gemma_wrapper_kwargs.items()]))
    data = jsonfile_to_dict(lookup_file("TMPDIR",
                                        token,
                                        metadata_filename))
    geno_file = lookup_file(environ_var="TMPDIR",
                            root_dir="genotype",
                            file_name=data.get("geno", ""))
    pheno_file = lookup_file(environ_var="TMPDIR",
                             root_dir=token,
                             file_name=data.get("geno", ""))
    cmd += f" -- -g {geno_file} -p {pheno_file}"
    if gemma_kwargs:
        cmd += (" "
                " ".join([f" -{key} {val}"
                          for key, val in gemma_kwargs.items()]))
    if gemma_args:
        cmd += (" "
                " ".join([f" {arg}" for arg in gemma_args]))
    return cmd


def queue_cmd(cmd: str, conn: Redis) -> str:
    """Given a command CMD, and a redis connection CONN, queue it in Redis
with an initial status of 'queued'.  The following status codes are
supported:

    queued:  Unprocessed; Still in the queue
    running: Still running
    success: Successful completion
    error:   Erroneous completion

    """
    if not conn.ping():
        raise RedisConnectionError
    unique_id = ("cmd::"
                 f"{datetime.now().strftime('%Y-%m-%d%H-%M%S-%M%S-')}"
                 f"{str(uuid4())}")
    for key, value in {"cmd": cmd,
                       "result": "",
                       "status": "queued"}.items():
        conn.hset(key, value, unique_id)
        conn.rpush("GN2::job-queue",
                   unique_id)
    return unique_id


def run_cmd(cmd: str) -> Dict:
    """Run CMD and return the CMD's status code and output as a dict"""
    results = subprocess.run(cmd, capture_output=True,
                             shell=True, check=False)
    out = str(results.stdout, 'utf-8')
    if results.returncode > 0:  # Error!
        out = str(results.stderr, 'utf-8')
    return {"code": results.returncode,
            "output": out}
