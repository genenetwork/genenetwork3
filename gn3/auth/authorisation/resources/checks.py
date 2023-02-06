"""Handle authorisation checks for resources"""
from uuid import UUID
from functools import reduce
from typing import Sequence

from gn3.auth import db
from gn3.auth.authentication.users import User

def __organise_privileges_by_resource_id__(rows):
    def __organise__(privs, row):
        resource_id = UUID(row["resource_id"])
        return {
            **privs,
            resource_id: (row["privilege_id"],) + privs.get(
                resource_id, tuple())
        }
    return reduce(__organise__, rows, {})

def authorised_for(conn: db.DbConnection, user: User, privileges: tuple[str],
                   resource_ids: Sequence[UUID]) -> dict[UUID, bool]:
    """
    Check whether `user` is authorised to access `resources` according to given
    `privileges`.
    """
    with db.cursor(conn) as cursor:
        cursor.execute(
            ("SELECT guror.*, rp.privilege_id FROM "
             "group_user_roles_on_resources AS guror "
             "INNER JOIN group_roles AS gr ON  "
             "(guror.group_id=gr.group_id AND guror.role_id=gr.role_id) "
             "INNER JOIN roles AS r ON gr.role_id=r.role_id "
             "INNER JOIN role_privileges AS rp ON r.role_id=rp.role_id "
             "WHERE guror.user_id=? "
             f"AND guror.resource_id IN ({', '.join(['?']*len(resource_ids))})"
             f"AND rp.privilege_id IN ({', '.join(['?']*len(privileges))})"),
            ((str(user.user_id),) + tuple(
                str(r_id) for r_id in resource_ids) + tuple(privileges)))
        resource_privileges = __organise_privileges_by_resource_id__(
            cursor.fetchall())
        authorised = tuple(resource_id for resource_id, res_privileges
                           in resource_privileges.items()
                           if all(priv in res_privileges
                                  for priv in privileges))
        return {
            resource_id: resource_id in authorised
            for resource_id in resource_ids
        }
