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


def queue_cmd(conn: Redis,
              job_queue: str,
              cmd: str,
              email: Optional[str] = None) -> str:
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
    for key, value in {"cmd": cmd, "result": "", "status": "queued"}.items():
        conn.hset(name=unique_id, key=key, value=value)
    if email:
        conn.hset(name=unique_id, key="email", value=email)
    return unique_id


def run_cmd(cmd: str) -> Dict:
    """Run CMD and return the CMD's status code and output as a dict"""
    results = subprocess.run(cmd, capture_output=True, shell=True, check=False)
    out = str(results.stdout, 'utf-8')
    if results.returncode > 0:  # Error!
        out = str(results.stderr, 'utf-8')
    return {"code": results.returncode, "output": out}
