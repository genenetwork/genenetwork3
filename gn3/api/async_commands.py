"""Endpoints and functions concerning commands run in external processes."""
import redis
from flask import jsonify, Blueprint

async_commands = Blueprint("async_commands", __name__)

@async_commands.route("/state/<command_id>")
def command_state(command_id):
    """Respond with the current state of command identified by `command_id`."""
    with redis.Redis(decode_responses=True) as rconn:
        state = rconn.hgetall(name=command_id)
        if not state:
            return jsonify(
                error="The command id provided does not exist.",
                status="error"), 404
        return jsonify(dict(state.items()))
