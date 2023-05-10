"""Handle user collections."""
import json

from redis import Redis

from .models import User

def user_collections(rconn: Redis, user: User) -> tuple:
    """Retrieve current user collections."""
    return tuple(json.loads(
        rconn.hget("collections", str(user.user_id)) or
        "[]"))

def old_user_collections(rconn: Redis, user: User) -> tuple:
    """
    Retrieve any old user collections and migrate them to new account.
    """
    collections = user_collections(rconn, user)
    old_user_accounts = [
        acct for acct in
        (json.loads(usr) for usr in rconn.hgetall("users").values())
        if acct.get("email_address", "") == user.email]
    for account in old_user_accounts:
        collections = collections + tuple(json.loads(
            rconn.hget("collections", account["user_id"]) or "[]"))
        rconn.hdel("collections", account["user_id"])

    rconn.hset(
        "collections", key=str(user.user_id), value=json.dumps(collections))
    return collections
