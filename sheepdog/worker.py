"""Daemon that processes commands"""
import os
import sys
import time
import logging
import argparse

import redis
import redis.connection

from gn3.loggers import setup_modules_logging

# Enable importing from one dir up: put as first to override any other globally
# accessible GN3
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))
logging.basicConfig(
    format=("%(asctime)s — %(filename)s:%(lineno)s — %(levelname)s: "
            "CommandWorker: %(message)s"))
logger = logging.getLogger(__name__)


def update_status(conn, cmd_id, status):
    """Helper to update command status"""
    conn.hset(name=f"{cmd_id}", key="status", value=f"{status}")


def make_incremental_backoff(init_val: float = 0.1, maximum: int = 420):
    """
    Returns a closure that can be used to increment the returned value up to
    `maximum` or reset it to `init_val`.
    """
    current = init_val

    def __increment_or_reset__(command: str, value: float = 0.1):
        nonlocal current
        if command == "reset":
            current = init_val
            return current

        if command == "increment":
            current = min(current + abs(value), maximum)
            return current

        return current

    return __increment_or_reset__


def run_jobs(conn, queue_name):
    """Process the redis using a redis connection, CONN"""
    # pylint: disable=E0401, C0415
    from gn3.commands import run_cmd
    cmd_id = (conn.lpop(queue_name) or b'').decode("utf-8")
    if bool(cmd_id):
        cmd = conn.hget(name=cmd_id, key="cmd")
        if cmd and (conn.hget(cmd_id, "status") == b"queued"):
            logger.debug("Updating status for job '%s' to 'running'", cmd_id)
            update_status(conn, cmd_id, "running")
            result = run_cmd(
                cmd.decode("utf-8"), env=conn.hget(name=cmd_id, key="env"))
            conn.hset(name=cmd_id, key="result", value=result.get("output"))
            if result.get("code") == 0:  # Success
                update_status(conn, cmd_id, "success")
            else:
                update_status(conn, cmd_id, "error")
                conn.hset(cmd_id, "stderr", result.get("output"))
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
    parser.add_argument(
        "--queue-name", default="GN3::job-queue", type=str,
        help="The redis list that holds the unique command ids")
    parser.add_argument(
        "--log-level", default="info", type=str,
        choices=("debug", "info", "warning", "error", "critical"),
        help="What level to output the logs at.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_cli_arguments()
    logger.setLevel(args.log_level.upper())
    logger.debug("Worker Script: Initialising worker")
    setup_modules_logging(
        logging.getLevelName(logger.getEffectiveLevel()),
        ("gn3.commands",))
    with redis.Redis() as redis_conn:
        if not args.daemon:
            logger.info("Worker Script: Running worker in one-shot mode.")
            run_jobs(redis_conn, args.queue_name)
            logger.debug("Job completed!")
        else:
            logger.debug("Worker Script: Running worker in daemon-mode.")
            sleep_time = make_incremental_backoff()
            while True:  # Daemon that keeps running forever:
                if run_jobs(redis_conn, args.queue_name):
                    logger.debug("Ran a job. Pausing for a while...")
                    time.sleep(sleep_time("reset"))
                    continue
                time.sleep(sleep_time(
                    "increment", sleep_time("return_current")))

    logger.info("Worker exiting …")
