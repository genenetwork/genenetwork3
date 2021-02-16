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
    cmd_id = str(conn.lpop("GN2::job-queue"))
    if bool(cmd_id):
        cmd = conn.hget("cmd", cmd_id)
        if cmd and (str(conn.hget(cmd, "status")) not in ["success",
                                                          "error"]):
            result = run_cmd(cmd)
            cmd.hset("result", result.get("output"), cmd_id)
            if result.get("code") == 0:  # Success
                cmd.hset("status", "success", cmd_id)
            else:
                cmd.hset("status", "error", cmd_id)


if __name__ == "__main__":
    redis_conn = redis.Redis()
    while True:  # Daemon that keeps running forever:
        run_jobs(redis_conn)
        time.sleep(0.1)
