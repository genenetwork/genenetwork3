"""Procedures used to work with the various bio-informatics cli
commands"""
import os
import sys
import json
import shlex
import pickle
import logging
import tempfile
import subprocess

from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union
from typing import Sequence
from uuid import uuid4

from flask import Flask, current_app
from redis.client import Redis  # Used only in type hinting

from pymonad.either import Either, Left, Right

from gn3.debug import __pk__
from gn3.chancy import random_string
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
    rscript = os.environ.get("RSCRIPT", "Rscript")
    cmd = f"{rscript} { rqtl_wrapper_cmd } " + " ".join(
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
    def __parse_method__(method):
        mthd = method.lower().replace("'", "")
        if "pearsons" in mthd:
            return "pearsons"
        if "spearmans" in mthd:
            return "spearmans"
        raise Exception(f"Invalid method '{method}'")# pylint: disable=[broad-exception-raised]

    prefix_cmd = (
        f"{sys.executable}", "-m", "scripts.partial_correlations",
        primary_trait, ",".join(control_traits), __parse_method__(method),
        current_app.config["SQL_URI"])
    if (
            kwargs.get("target_database") is not None
            and kwargs.get("target_traits") is None):
        return compose_pcorrs_command_for_database(prefix_cmd, **kwargs)
    if (
            kwargs.get("target_database") is None
            and kwargs.get("target_traits") is not None):
        return compose_pcorrs_command_for_selected_traits(prefix_cmd, **kwargs)
    raise Exception("Invalid state: I don't know what command to generate!")# pylint: disable=[broad-exception-raised]

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

def run_sample_corr_cmd(method, this_trait_data, target_dataset_data):
    "Run the sample correlations in an external process, returning the results."
    with tempfile.TemporaryDirectory() as tempdir:
        traitfile = f"{tempdir}/traitfile_{random_string(10)}"
        targetfile = f"{tempdir}/targetdb_{random_string(10)}"
        destfile = f"{tempdir}/corrs_{random_string(10)}"
        with open(traitfile, "wb") as trtfl:
            pickle.dump(this_trait_data, trtfl)

        with open(targetfile, "wb") as targfl:
            pickle.dump(target_dataset_data, targfl)

            subprocess.run(
                ["python3", "-m", "scripts.sample_correlations", method,
                 traitfile, targetfile, destfile],
                check=True)

            with open(destfile, "rb") as dstfl:
                correlation_results = pickle.load(dstfl)

    return correlation_results

def run_cmd(cmd: str, success_codes: Tuple = (0,), env: Optional[str] = None) -> Dict:
    """Run CMD and return the CMD's status code and output as a dict"""
    try:
        parsed_cmd = json.loads(cmd)
    except json.decoder.JSONDecodeError as _jderr:
        parsed_cmd = shlex.split(cmd)

    parsed_env = (json.loads(env) if env is not None else None)

    results = subprocess.run(
        parsed_cmd, capture_output=True, shell=isinstance(parsed_cmd, str),
        check=False, env=parsed_env)
    out = str(results.stdout, 'utf-8')
    if results.returncode not in success_codes:  # Error!
        out = str(results.stderr, 'utf-8')
        (# We do not always run this within an app context
            current_app.logger.debug if current_app else logging.debug)(out)
    return {"code": results.returncode, "output": out}


def compute_job_queue(app: Flask) -> str:
    """Use the app configurations to compute the job queue"""
    app_env = app.config["APPLICATION_ENVIRONMENT"]
    job_queue = app.config["REDIS_JOB_QUEUE"]
    if bool(app_env):
        return f"{app_env}::{job_queue}"
    return job_queue


def run_async_cmd(
        conn: Redis, job_queue: str, cmd: Union[str, Sequence[str]],
        options: Optional[Dict[str, Any]] = None,
        log_level: str = "info") -> str:
    """A utility function to call `gn3.commands.queue_cmd` function and run the
    worker in the `one-shot` mode."""
    email = options.get("email") if options else None
    env = options.get("env") if options else None
    cmd_id = queue_cmd(conn, job_queue, cmd, email, env)
    worker_command = [
        sys.executable,
        "-m", "sheepdog.worker",
        "--queue-name", job_queue,
        "--log-level", log_level
    ]
    logging.debug("Launching the worker: %s", worker_command)
    subprocess.Popen( # pylint: disable=[consider-using-with]
        worker_command)
    return cmd_id


def monadic_run_cmd(cmd) -> Either:
    """Run a given command and return it's results as an Either monad"""
    result = ""
    try:
        result = subprocess.run(cmd,
                                capture_output=True,
                                check=True).stdout.decode()
    # This command does not exist
    except FileNotFoundError as excpt:
        return Left({
            "command": cmd,
            "error": str(excpt),
        })
    except subprocess.CalledProcessError as excpt:
        return Left({
            "command": cmd,
            "error": str(excpt),
        })
    return Right(result)
