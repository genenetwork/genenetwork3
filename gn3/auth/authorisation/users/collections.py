"""Handle user collections."""
import uuid
import json

from redis import Redis
from email_validator import validate_email, EmailNotValidError

from .models import User

def __valid_email__(email:str) -> bool:
    """Check for email validity."""
    try:
        validate_email(email, check_deliverability=True)
    except EmailNotValidError as _enve:
        return False
    return True

def __toggle_boolean_field__(
        rconn: Redis, email: str, field: str):
    """Toggle the valuen of a boolean field"""
    mig_dict = json.loads(rconn.hget("migratable-accounts", email) or "{}")
    if bool(mig_dict):
        rconn.hset("migratable-accounts", email,
                   {**mig_dict, field: not mig_dict.get(field, True)})

def __build_email_uuid_bridge__(rconn: Redis):
    """
    Build a connection between new accounts and old user accounts.

    The only thing that is common between the two is the email address,
    therefore, we use that to link the two items.
    """
    old_accounts = {
        account["email_address"]: {
            "user_id": account["user_id"],
            "collections-migrated": False,
            "resources_migrated": False
        } for account in (
            acct for acct in
            (json.loads(usr) for usr in rconn.hgetall("users").values())
            if (bool(acct.get("email_address", False)) and
                __valid_email__(acct["email_address"])))
    }
    if bool(old_accounts):
        rconn.hset("migratable-accounts", mapping={
            key: json.dumps(value) for key,value in old_accounts.items()
        })
    return old_accounts

def __retrieve_old_accounts__(rconn: Redis) -> dict:
    accounts = rconn.hgetall("migratable-accounts")
    if accounts:
        return {
            key: json.loads(value) for key, value in accounts.items()
        }
    return __build_email_uuid_bridge__(rconn)

def __retrieve_old_user_collections__(rconn: Redis, old_user_id: uuid.UUID) -> tuple:
    """Retrieve any old collections relating to the user."""
    return tuple(json.loads(rconn.hget("collections", old_user_id) or "[]"))

def user_collections(rconn: Redis, user: User) -> tuple:
    """Retrieve current user collections."""
    collections = tuple(json.loads(
        rconn.hget("collections", str(user.user_id)) or
        "[]"))
    old_accounts = __retrieve_old_accounts__(rconn)
    if (user.email in old_accounts and
        not old_accounts[user.email]["collections-migrated"]):
        old_user_id = old_accounts[user.email]["user_id"]
        collections = tuple(set(collections + __retrieve_old_user_collections__(
            rconn, uuid.UUID(old_user_id))))
        rconn.hdel("collections", old_user_id)
        __toggle_boolean_field__(rconn, user.email, "collections-migrated")
        rconn.hset(
            "collections", key=user.user_id, value=json.dumps(collections))
    return collections
