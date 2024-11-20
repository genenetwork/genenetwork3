""" File contains  computational for running rqtl2"""

import uuid
import datetime


def create_rqtl2_task(redisconn):
    """Function to create a rqtl2 task and set it in  redis"""
    task_id = str(uuid.uuid4())
    entries = {
        "task_id": task_id,
        "created": datetime.now(),
        "status": "queued",
        "stdout": "",
        "stderr": "",
    }
    redisconn.hset(task_id, mapping=entries)


def compose_rqtl2_cmd(rqtl_wrapper_cmd: str,
                      rqtl_wrapper_kwargs) -> str:
    """Compose a valid R/qtl command given the correct input"""
    # Add kwargs with values
    return f"Rscript { rqtl_wrapper_cmd } " + " ".join(
        [f"--{key} {val}" for key, val in rqtl_wrapper_kwargs.items()])
