
"""this module is an interface mapper for gn-llm\
and gn-auth +  api key for the llm"""
from functools import wrap


def authenticator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.current_user:
            return jsonify({"error": "user needs to be authenticated"}), 403
        return f(*args, **kwargs)
    return decorated_function
