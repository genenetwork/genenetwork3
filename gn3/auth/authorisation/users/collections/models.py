"""Handle user collections."""
import json
from uuid import UUID, uuid4
from datetime import datetime

from redis import Redis
from email_validator import validate_email, EmailNotValidError

from gn3.auth.authorisation.errors import InvalidData, NotFoundError

from ..models import User

__OLD_REDIS_COLLECTIONS_KEY__ = "collections"
__REDIS_COLLECTIONS_KEY__ = "collections2"

class CollectionJSONEncoder(json.JSONEncoder):
    """Serialise collection objects into JSON."""
    def default(self, obj):# pylint: disable=[arguments-renamed]
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.strftime("%b %d %Y %I:%M%p")
        return json.JSONEncoder.default(self, obj)

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
                   json.dumps({**mig_dict, field: not mig_dict.get(field, True)}))

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

def parse_collection(coll: dict) -> dict:
    """Parse the collection as persisted in redis to a usable python object."""
    created = coll.get("created", coll.get("created_timestamp"))
    changed = coll.get("changed", coll.get("changed_timestamp"))
    return {
        "id": UUID(coll["id"]),
        "name": coll["name"],
        "created": datetime.strptime(created, "%b %d %Y %I:%M%p"),
        "changed": datetime.strptime(changed, "%b %d %Y %I:%M%p"),
        "num_members": int(coll["num_members"]),
        "members": coll["members"]
    }

def dump_collection(pythoncollection: dict) -> str:
    """Convert the collection from a python object to a json string."""
    return json.dumps(pythoncollection, cls=CollectionJSONEncoder)

def __retrieve_old_user_collections__(rconn: Redis, old_user_id: UUID) -> tuple:
    """Retrieve any old collections relating to the user."""
    return tuple(parse_collection(coll) for coll in
                 json.loads(rconn.hget(
                     __OLD_REDIS_COLLECTIONS_KEY__, str(old_user_id)) or "[]"))

def user_collections(rconn: Redis, user: User) -> tuple[dict, ...]:
    """Retrieve current user collections."""
    collections = tuple(parse_collection(coll) for coll in json.loads(
        rconn.hget(__REDIS_COLLECTIONS_KEY__, str(user.user_id)) or
        "[]"))
    old_accounts = __retrieve_old_accounts__(rconn)
    if (user.email in old_accounts and
        not old_accounts[user.email]["collections-migrated"]):
        old_user_id = old_accounts[user.email]["user_id"]
        collections = tuple({
            coll["id"]: coll for coll in (
                collections + __retrieve_old_user_collections__(
                    rconn, UUID(old_user_id)))
        }.values())
        __toggle_boolean_field__(rconn, user.email, "collections-migrated")
        rconn.hset(
            __REDIS_COLLECTIONS_KEY__,
            key=str(user.user_id),
            value=json.dumps(collections, cls=CollectionJSONEncoder))
    return collections

def save_collections(rconn: Redis, user: User, collections: tuple[dict, ...]) -> tuple[dict, ...]:
    """Save the `collections` to redis."""
    rconn.hset(
        __REDIS_COLLECTIONS_KEY__,
        str(user.user_id),
        json.dumps(collections, cls=CollectionJSONEncoder))
    return collections

def add_to_user_collections(rconn: Redis, user: User, collection: dict) -> dict:
    """Add `collection` to list of user collections."""
    ucolls = user_collections(rconn, user)
    save_collections(rconn, user, ucolls + (collection,))
    return collection

def create_collection(rconn: Redis, user: User, name: str, traits: tuple) -> dict:
    """Create a new collection."""
    now = datetime.utcnow()
    return add_to_user_collections(rconn, user, {
        "id": uuid4(),
        "name": name,
        "created": now,
        "changed": now,
        "num_members": len(traits),
        "members": traits
    })

def get_collection(rconn: Redis, user: User, collection_id: UUID) -> dict:
    """Retrieve the collection with ID `collection_id`."""
    colls = tuple(coll for coll in user_collections(rconn, user)
                  if coll["id"] == collection_id)
    if len(colls) == 0:
        raise NotFoundError(
            f"Could not find a collection with ID `{collection_id}` for user "
            f"with ID `{user.user_id}`")
    if len(colls) > 1:
        err = InvalidData(
            "More than one collection was found having the ID "
            f"`{collection_id}` for user with ID `{user.user_id}`.")
        err.error_code = 513
        raise err
    return colls[0]

def __raise_if_collections_empty__(user: User, collections: tuple[dict, ...]):
    """Raise an exception if no collections are found for `user`."""
    if len(collections) < 1:
        raise NotFoundError(f"No collections found for user `{user.user_id}`")

def __raise_if_not_single_collection__(
        user: User, collection_id: UUID, collections: tuple[dict, ...]):
    """
    Raise an exception there is zero, or more than one collection for `user`.
    """
    if len(collections) == 0:
        raise NotFoundError(f"No collections found for user `{user.user_id}` "
                            f"with ID `{collection_id}`.")
    if len(collections) > 1:
        err = InvalidData(
            "More than one collection was found having the ID "
            f"`{collection_id}` for user with ID `{user.user_id}`.")
        err.error_code = 513
        raise err

def delete_collections(rconn: Redis,
                       user: User,
                       collection_ids: tuple[UUID, ...]) -> tuple[dict, ...]:
    """
    Delete collections with the given `collection_ids` returning the deleted
    collections.
    """
    ucolls = user_collections(rconn, user)
    save_collections(
        rconn,
        user,
        tuple(coll for coll in ucolls if coll["id"] not in collection_ids))
    return tuple(coll for coll in ucolls if coll["id"] in collection_ids)

def add_traits(rconn: Redis,
               user: User,
               collection_id: UUID,
               traits: tuple[str, ...]) -> dict:
    """
    Add `traits` to the `user` collection identified by `collection_id`.

    Returns: The collection with the new traits added.
    """
    ucolls = user_collections(rconn, user)
    __raise_if_collections_empty__(user, ucolls)

    mod_col = tuple(coll for coll in ucolls if coll["id"] == collection_id)
    __raise_if_not_single_collection__(user, collection_id, mod_col)
    new_members = tuple(set(tuple(mod_col[0]["members"]) + traits))
    new_coll = {
        **mod_col[0],
        "members": new_members,
        "num_members": len(new_members)
    }
    save_collections(
        rconn,
        user,
        (tuple(coll for coll in ucolls if coll["id"] != collection_id) +
         (new_coll,)))
    return new_coll

def remove_traits(rconn: Redis,
                  user: User,
                  collection_id: UUID,
                  traits: tuple[str, ...]) -> dict:
    """
    Remove `traits` from the `user` collection identified by `collection_id`.

    Returns: The collection with the specified `traits` removed.
    """
    ucolls = user_collections(rconn, user)
    __raise_if_collections_empty__(user, ucolls)

    mod_col = tuple(coll for coll in ucolls if coll["id"] == collection_id)
    __raise_if_not_single_collection__(user, collection_id, mod_col)
    new_members = tuple(
        trait for trait in mod_col[0]["members"] if trait not in traits)
    new_coll = {
        **mod_col[0],
        "members": new_members,
        "num_members": len(new_members)
    }
    save_collections(
        rconn,
        user,
        (tuple(coll for coll in ucolls if coll["id"] != collection_id) +
         (new_coll,)))
    return new_coll

def change_name(rconn: Redis,
                user: User,
                collection_id: UUID,
                new_name: str) -> dict:
    """
    Change the collection's name.

    Returns: The collection with the new name.
    """
    ucolls = user_collections(rconn, user)
    __raise_if_collections_empty__(user, ucolls)

    mod_col = tuple(coll for coll in ucolls if coll["id"] == collection_id)
    __raise_if_not_single_collection__(user, collection_id, mod_col)

    new_coll = {**mod_col[0], "name": new_name}
    save_collections(
        rconn,
        user,
        (tuple(coll for coll in ucolls if coll["id"] != collection_id) +
         (new_coll,)))
    return new_coll
