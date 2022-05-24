"""Daemon that processes commands"""
import os
import sys
import time
import argparse

import redis
import redis.connection

# Enable importing from one dir up: put as first to override any other globally
# accessible GN3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def update_status(conn, cmd_id, status):
    """Helper to update command status"""
    conn.hset(name=f"{cmd_id}", key="status", value=f"{status}")

def make_incremental_backoff(init_val: float=0.1, maximum: int=420):
    """
    Returns a closure that can be used to increment the returned value up to
    `maximum` or reset it to `init_val`.
    """
    current = init_val

    def __increment_or_reset__(command: str, value: float=0.1):
        nonlocal current
        if command == "reset":
            current = init_val
            return current

        if command == "increment":
            current = min(current + abs(value), maximum)
            return current

        return current

    return __increment_or_reset__

def run_jobs(conn, queue_name: str = "GN3::job-queue"):
    """Process the redis using a redis connection, CONN"""
    # pylint: disable=E0401, C0415
    from gn3.commands import run_cmd
    cmd_id = (conn.lpop(queue_name) or b'').decode("utf-8")
    if bool(cmd_id):
        cmd = conn.hget(name=cmd_id, key="cmd")
        if cmd and (conn.hget(cmd_id, "status") == b"queued"):
            update_status(conn, cmd_id, "running")
            result = run_cmd(
                cmd.decode("utf-8"), env=conn.hget(name=cmd_id, key="env"))
            conn.hset(name=cmd_id, key="result", value=result.get("output"))
            if result.get("code") == 0:  # Success
                update_status(conn, cmd_id, "success")
            else:
                update_status(conn, cmd_id, "error")
        return cmd_id
    return None

def parse_cli_arguments():
    """Parse the command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run asynchronous (service) commands.")
    parser.add_argument(
        "--daemon", default=False, action="store_true",
        help=(
            "Run process as a daemon instead of the default 'one-shot' "
            "process"))
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_cli_arguments()
    with redis.Redis() as redis_conn:
        if not args.daemon:
            run_jobs(redis_conn)
        else:
            sleep_time = make_incremental_backoff()
            while True:  # Daemon that keeps running forever:
                if run_jobs(redis_conn):
                    time.sleep(sleep_time("reset"))
                    continue
                time.sleep(sleep_time("increment", sleep_time("return_current")))
