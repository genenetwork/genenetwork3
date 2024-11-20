""" File contains  computational for running rqtl2"""

import uuid
import datetime
import subprocess


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


def compose_rqtl2_cmd(rqtl2_script_path: str,
                      rqtl_wrapper_kwargs) -> str:
    """Compose a valid R/qtl command given the correct input"""
    # Add kwargs with values
    return f"Rscript {rqtl2_script_path} " + " ".join(
        [f"--{key} {val}" for key, val in rqtl_wrapper_kwargs.items()])


def execute_script(task_id, redis_conn, script_path, rqtl_kwargs):
    """Execute the Rscript and update redis with real time output and status"""
    # update redis with status
    redis_conn.hset(task_id, "status", "Running")
    redis_conn.hset(task_id, "stdout", "")
    redis_conn.hset(task_id, "stderr", "")

    entries = {
        "status": "Running",
    }

    # todo! check if the keys for this are replaced
    redis_conn.hset(task_id, mapping=entries)
    # get this from configa
    # todo! make assertions that the script exists
    try:
        rqtl2_script_path = "./scripts/rqtl2_wrapper.R"
        cmd = compose_rqtl2_cmd(rqtl2_script_path, rqtl_kwargs)
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT
                                   )
        for line in iter(process.stdout.readline, ""):
            # insert this to redis store
            # ??? not sure we should decode this
            redis_conn.hset(task_id, "stdout",
                            redis_conn.hget(task_id, "stdout").decode() + line)
        process.stdout.close()

        stderr = process.stderror.read()
        redis_conn.hset(task_id, "stderr", stderr)
        process.stderror.close()
        # process task get id
        if process.returncode == 0:
            redis_conn.hset(task_id, "status", "Completed")
        else:
            redis_conn.hset(task_id, "status", "Failed")
        return {}
    except Exception as error:
        redis_conn.hset(task_id, "status", "Failed")
        raise error
