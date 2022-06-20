"""Procedures used to work with the various bio-informatics cli
commands"""
import sys
import json
import subprocess

from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union
from typing import Sequence
from uuid import uuid4
from redis.client import Redis  # Used only in type hinting

from gn3.exceptions import RedisConnectionError


def compose_gemma_cmd(gemma_wrapper_cmd: str = "gemma-wrapper",
                      gemma_wrapper_kwargs: Optional[Dict] = None,
                      gemma_kwargs: Optional[Dict] = None,
                      gemma_args: Optional[List] = None) -> str:
    """Compose a valid GEMMA command given the correct values"""
    cmd = f"{gemma_wrapper_cmd} --json"
    if gemma_wrapper_kwargs:
        cmd += " "  # Add extra space between commands
        cmd += " ".join(
            [f"--{key} {val}" for key, val in gemma_wrapper_kwargs.items()])
    cmd += " -- "
    if gemma_kwargs:
        cmd += " ".join([f"-{key} {val}" for key, val in gemma_kwargs.items()])
    if gemma_args:
        cmd += " "
        cmd += " ".join([f"{arg}" for arg in gemma_args])
    return cmd

def compose_rqtl_cmd(rqtl_wrapper_cmd: str,
                     rqtl_wrapper_kwargs: Dict,
                     rqtl_wrapper_bool_kwargs: list) -> str:
    """Compose a valid R/qtl command given the correct input"""
    # Add kwargs with values
    cmd = f"Rscript { rqtl_wrapper_cmd } " + " ".join(
        [f"--{key} {val}" for key, val in rqtl_wrapper_kwargs.items()])

    # Add boolean kwargs (kwargs that are either on or off, like --interval)
    if rqtl_wrapper_bool_kwargs:
        cmd += " "
        cmd += " ".join([f"--{val}" for val in rqtl_wrapper_bool_kwargs])

    return cmd

def compose_pcorrs_command_for_selected_traits(
        prefix_cmd: Tuple[str, ...], target_traits: Tuple[str, ...]) -> Tuple[
            str, ...]:
    """Build command for partial correlations against selected traits."""
    return prefix_cmd + ("against-traits", ",".join(target_traits))

def compose_pcorrs_command_for_database(
        prefix_cmd: Tuple[str, ...], target_database: str,
        criteria: int = 500) -> Tuple[str, ...]:
    """Build command for partial correlations against an entire dataset."""
    return prefix_cmd + (
        "against-db", f"{target_database}", f"--criteria={criteria}")

def compose_pcorrs_command(
        primary_trait: str, control_traits: Tuple[str, ...], method: str,
        **kwargs):
    """Compose the command to run partias correlations"""
    prefix_cmd = (
        f"{sys.executable}", "-m", "scripts.partial_correlations",
        primary_trait, ",".join(control_traits), method)
    if (
            kwargs.get("target_database") is not None
            and kwargs.get("target_traits") is None):
        return compose_pcorrs_command_for_database(prefix_cmd, **kwargs)
    if (
            kwargs.get("target_database") is None
            and kwargs.get("target_traits") is not None):
        return compose_pcorrs_command_for_selected_traits(prefix_cmd, **kwargs)
    raise Exception("Invalid state: I don't know what command to generate!")

def queue_cmd(conn: Redis,
              job_queue: str,
              cmd: Union[str, Sequence[str]],
              email: Optional[str] = None,
              env: Optional[dict] = None) -> str:
    """Given a command CMD; (optional) EMAIL; and a redis connection CONN, queue
it in Redis with an initial status of 'queued'.  The following status codes
are supported:

    queued:  Unprocessed; Still in the queue
    running: Still running
    success: Successful completion
    error:   Erroneous completion

Returns the name of the specific redis hash for the specific task.

    """
    if not conn.ping():
        raise RedisConnectionError
    unique_id = ("cmd::"
                 f"{datetime.now().strftime('%Y-%m-%d%H-%M%S-%M%S-')}"
                 f"{str(uuid4())}")
    conn.rpush(job_queue, unique_id)
    for key, value in {
            "cmd": json.dumps(cmd), "result": "", "status": "queued"}.items():
        conn.hset(name=unique_id, key=key, value=value)
    if email:
        conn.hset(name=unique_id, key="email", value=email)
    if env:
        conn.hset(name=unique_id, key="env", value=json.dumps(env))
    return unique_id

def run_cmd(cmd: str, success_codes: Tuple = (0,), env: str = None) -> Dict:
    """Run CMD and return the CMD's status code and output as a dict"""
    parsed_cmd = json.loads(cmd)
    parsed_env = (json.loads(env) if env is not None else None)
    results = subprocess.run(
        parsed_cmd, capture_output=True, shell=isinstance(parsed_cmd, str),
        check=False, env=parsed_env)
    out = str(results.stdout, 'utf-8')
    if results.returncode not in success_codes:  # Error!
        out = str(results.stderr, 'utf-8')
    return {"code": results.returncode, "output": out}

def run_async_cmd(
        conn: Redis, job_queue: str, cmd: Union[str, Sequence[str]],
        email: Optional[str] = None, env: Optional[dict] = None) -> str:
    """A utility function to call `gn3.commands.queue_cmd` function and run the
    worker in the `one-shot` mode."""
    cmd_id = queue_cmd(conn, job_queue, cmd, email, env)
    subprocess.Popen([f"{sys.executable}", "-m", "sheepdog.worker"]) # pylint: disable=[consider-using-with]
    return cmd_id
