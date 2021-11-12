"""Methods for interacting with gn-proxy."""
import functools
import json
import uuid
import datetime

from urllib.parse import urljoin
from enum import Enum, unique
from typing import Dict, List, Optional, Union

from redis import Redis
import requests


@functools.total_ordering
class OrderedEnum(Enum):
    """A class that ordered Enums in order of position"""
    @classmethod
    @functools.lru_cache(None)
    def _member_list(cls):
        return list(cls)

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            member_list = self.__class__._member_list()
            return member_list.index(self) < member_list.index(other)
        return NotImplemented


@unique
class DataRole(OrderedEnum):
    """Enums for Data Access"""
    NO_ACCESS = "no-access"
    VIEW = "view"
    EDIT = "edit"


@unique
class AdminRole(OrderedEnum):
    """Enums for Admin status"""
    NOT_ADMIN = "not-admin"
    EDIT_ACCESS = "edit-access"
    EDIT_ADMINS = "edit-admins"


def get_user_membership(conn: Redis, user_id: str,
                        group_id: str) -> Dict:
    """Return a dictionary that indicates whether the `user_id` is a
    member or admin of `group_id`.

    Args:
      - conn: a Redis Connection with the responses decoded.
      - user_id: a user's unique id
        e.g. '8ad942fe-490d-453e-bd37-56f252e41603'
      - group_id: a group's unique id
      e.g. '7fa95d07-0e2d-4bc5-b47c-448fdc1260b2'

    Returns:
      A dict indicating whether the user is an admin or a member of
      the group: {"member": True, "admin": False}

    """
    results = {"member": False, "admin": False}
    for key, value in conn.hgetall('groups').items():
        if key == group_id:
            group_info = json.loads(value)
            if user_id in group_info.get("admins"):
                results["admin"] = True
            if user_id in group_info.get("members"):
                results["member"] = True
            break
    return results


def get_highest_user_access_role(
        resource_id: str,
        user_id: str,
        gn_proxy_url: str = "http://localhost:8080") -> Dict:
    """Get the highest access roles for a given user

    Args:
      - resource_id: The unique id of a given resource.
      - user_id: The unique id of a given user.
      - gn_proxy_url: The URL where gn-proxy is running.

    Returns:
      A dict indicating the highest access role the user has.

    """
    role_mapping: Dict[str, Union[DataRole, AdminRole]] = {}
    for data_role, admin_role in zip(DataRole, AdminRole):
        role_mapping.update({data_role.value: data_role, })
        role_mapping.update({admin_role.value: admin_role, })
    access_role = {}
    response = requests.get(urljoin(gn_proxy_url,
                                    ("available?resource="
                                     f"{resource_id}&user={user_id}")))
    for key, value in json.loads(response.content).items():
        access_role[key] = max(map(lambda role: role_mapping[role], value))
    return access_role


def get_groups_by_user_uid(user_uid: str, conn: Redis) -> Dict:
    """Given a user uid, get the groups in which they are a member or admin of.

    Args:
      - user_uid: A user's unique id
      - conn: A redis connection

    Returns:
      - A dictionary containing the list of groups the user is part of e.g.:
        {"admin": [], "member": ["ce0dddd1-6c50-4587-9eec-6c687a54ad86"]}
    """
    admin = []
    member = []
    for uuid, group_info in conn.hgetall("groups").items():
        group_info = json.loads(group_info)
        group_info["uuid"] = uuid
        if user_uid in group_info.get('admins'):
            admin.append(group_info)
        if user_uid in group_info.get('members'):
            member.append(group_info)
    return {
        "admin": admin,
        "member": member,
    }


def get_user_info_by_key(key: str, value: str,
                         conn: Redis) -> Optional[Dict]:
    """Given a key, get a user's information if value is matched"""
    if key != "user_id":
        for uuid, user_info in conn.hgetall("users").items():
            user_info = json.loads(user_info)
            if (key in user_info and
                user_info.get(key) == value):
                user_info["user_id"] = uuid
                return user_info
    elif key == "user_id":
        if user_info := conn.hget("users", value):
            user_info = json.loads(user_info)
            user_info["user_id"] = value
            return user_info
    return None


def create_group(conn: Redis, group_name: Optional[str],
                 admin_user_uids: List = [],
                 member_user_uids: List = []) -> Optional[Dict]:
    """Create a group given the group name, members and admins of that group."""
    if group_name and bool(admin_user_uids + member_user_uids):
        timestamp = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
        group = {
            "id": (group_id := str(uuid.uuid4())),
            "admins": admin_user_uids,
            "members": member_user_uids,
            "name": group_name,
            "created_timestamp": timestamp,
            "changed_timestamp": timestamp,
        }
        conn.hset("groups", group_id, json.dumps(group))
        return group
