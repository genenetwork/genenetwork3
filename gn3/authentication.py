"""Methods for interacting with gn-proxy."""
import functools
import json
from urllib.parse import urljoin
from enum import Enum, unique
from typing import Dict

import redis
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


def get_user_membership(conn: redis.Redis, user_id: str,
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
    role_mapping = {}
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
