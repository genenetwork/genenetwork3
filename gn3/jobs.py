"""Handle external processes in a consistent manner."""
import json
from typing import Any
from uuid import UUID, uuid4
from datetime import datetime

from redis import Redis
from pymonad.either import Left, Right, Either

from gn3 import json_encoders_decoders as jed

JOBS_NAMESPACE = "GN3::JOBS"

class InvalidCommand(Exception):
    """Raise if the command to run is invalid."""

def job_key(job_id: UUID, namespace_prefix: str = JOBS_NAMESPACE):
    """Build the namespace key for a specific job."""
    return f"{namespace_prefix}::{job_id}"

def job(redisconn: Redis, job_id: UUID) -> Either:
    """Retrive the job details of a job identified by `job_id`."""
    the_job = redisconn.hgetall(job_key(job_id))
    if the_job:
        return Right({
            key: json.loads(value, object_hook=jed.custom_json_decoder)
            for key, value in the_job.items()# type: ignore[union-attr]
        })
    return Left({
        "error": "NotFound",
        "error_description": f"Job '{job_id}' was not found."
    })

def __command_valid__(job_command: Any) -> Either:
    if not isinstance(job_command, list):
        return Left({
            "error": "InvalidJobCommand",
            "error_description": "The job command MUST be a list."
        })
    if not all((isinstance(val, str) for val in job_command)):
        return Left({
            "error": "InvalidJobCommand",
            "error_description": "All parts of the command MUST be strings."
        })
    return Right(job_command)

def create_job(redisconn: Redis, job_details: dict[str, Any]) -> UUID:
    """Create a new job and put it on Redis."""
    def __create__(_job_command):
        job_id = job_details.get("job_id", uuid4())
        redisconn.hset(job_key(job_id), mapping={
            key: json.dumps(value, cls=jed.CustomJSONEncoder) for key, value in {
                **job_details, "job_id": job_id, "created": datetime.now(),
                "status": "queued"
            }.items()
        })
        return job_id
    def __raise__(err):
        raise InvalidCommand(err["error_description"])
    return __command_valid__(job_details.get("command")).either(
        __raise__, __create__)
