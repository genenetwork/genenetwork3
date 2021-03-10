"""Daemon that processes commands"""
import os
import sys
import time
import redis
import redis.connection


# Enable importing from one dir up since gn3 isn't installed as a globally
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__),
                                 '..')))


def run_jobs(conn):
    """Process the redis using a redis connection, CONN"""
    # pylint: disable=E0401, C0415
    from gn3.commands import run_cmd
    cmd_id = str(conn.lpop("GN3::job-queue"))
    if bool(cmd_id):
        cmd = conn.hget(name=cmd_id, key="cmd")
        if cmd and (str(conn.hget(cmd, "status")) == "queued"):
            result = run_cmd(cmd)
            conn.hset(name=cmd_id, key="result", value=result.get("output"))
            if result.get("code") == 0:  # Success
                conn.hset(name=cmd_id, key="status", value="success")
            else:
                conn.hset(name=cmd_id, key="status", value="error")


if __name__ == "__main__":
    redis_conn = redis.Redis()
    while True:  # Daemon that keeps running forever:
        run_jobs(redis_conn)
        time.sleep(0.1)
