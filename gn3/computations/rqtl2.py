""" File contains  computational for running rqtl2"""

import uuid
import datetime


def create_rqtl2_task(redisconn):
    """Function to create a rqtl2 task and set it in  redis"""
    task_id = str(uuid.uuid4())
    entries = {
        "job_id": task_id,
        "created": datetime.now(),
        "status": "queued",
        "stdout": "",
        "stderr": "",
    }
    redisconn.hset(task_id, mapping=entries)
