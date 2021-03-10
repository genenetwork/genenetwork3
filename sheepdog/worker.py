"""Daemon that processes commands"""
import os
import sys
import time
import redis
import redis.connection

# Enable importing from one dir up since gn3 isn't installed as a globally
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_jobs(conn):
    """Process the redis using a redis connection, CONN"""
    # pylint: disable=E0401, C0415
    from gn3.commands import run_cmd
    cmd_id = (conn.lpop("GN3::job-queue") or b'').decode("utf-8")
    if bool(cmd_id):
        cmd = conn.hget(name=cmd_id, key="cmd")
        if cmd and (conn.hget(cmd_id, "status") == b"queued"):
            result = run_cmd(cmd.decode("utf-8"))
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
