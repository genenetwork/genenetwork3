"""Handle the management of resources."""
import json
import sqlite3
from uuid import UUID, uuid4
from functools import partial
from typing import Any, Dict, Sequence, NamedTuple

from gn3.auth import db
from gn3.auth.dictify import dictify
from gn3.auth.authentication.users import User
from gn3.auth.db_utils import with_db_connection

from .checks import authorised_for

from ..checks import authorised_p
from ..errors import NotFoundError, AuthorisationError
from ..groups.models import Group, user_group, group_by_id, is_group_leader

class MissingGroupError(AuthorisationError):
    """Raised for any resource operation without a group."""

class ResourceCategory(NamedTuple):
    """Class representing a resource category."""
    resource_category_id: UUID
    resource_category_key: str
    resource_category_description: str

    def dictify(self) -> dict[str, Any]:
        """Return a dict representation of `ResourceCategory` objects."""
        return {
            "resource_category_id": self.resource_category_id,
            "resource_category_key": self.resource_category_key,
            "resource_category_description": self.resource_category_description
        }

class Resource(NamedTuple):
    """Class representing a resource."""
    group: Group
    resource_id: UUID
    resource_name: str
    resource_category: ResourceCategory
    public: bool
    resource_data: Sequence[dict[str, Any]] = tuple()

    def dictify(self) -> dict[str, Any]:
        """Return a dict representation of `Resource` objects."""
        return {
            "group": dictify(self.group), "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "resource_category": dictify(self.resource_category),
            "public": self.public,
            "resource_data": self.resource_data
        }

def __assign_resource_owner_role__(cursor, resource, user):
    """Assign `user` the 'Resource Owner' role for `resource`."""
    cursor.execute(
        "SELECT gr.* FROM group_roles AS gr INNER JOIN roles AS r "
        "ON gr.role_id=r.role_id WHERE r.role_name='resource-owner'")
    role = cursor.fetchone()
    if not role:
        cursor.execute("SELECT * FROM roles WHERE role_name='resource-owner'")
        role = cursor.fetchone()
        cursor.execute(
            "INSERT INTO group_roles VALUES "
            "(:group_role_id, :group_id, :role_id)",
            {"group_role_id": str(uuid4()),
             "group_id": str(resource.group.group_id),
             "role_id": role["role_id"]})

    cursor.execute(
            "INSERT INTO group_user_roles_on_resources "
            "VALUES ("
            ":group_id, :user_id, :role_id, :resource_id"
            ")",
            {"group_id": str(resource.group.group_id),
             "user_id": str(user.user_id),
             "role_id": role["role_id"],
             "resource_id": str(resource.resource_id)})

@authorised_p(("group:resource:create-resource",),
              error_description="Insufficient privileges to create a resource",
              oauth2_scope="profile resource")
def create_resource(
        conn: db.DbConnection, resource_name: str,
        resource_category: ResourceCategory, user: User) -> Resource:
    """Create a resource item."""
    with db.cursor(conn) as cursor:
        group = user_group(cursor, user).maybe(
            False, lambda grp: grp)# type: ignore[misc, arg-type]
        if not group:
            raise MissingGroupError(
                "User with no group cannot create a resource.")
        resource = Resource(group, uuid4(), resource_name, resource_category, False)
        cursor.execute(
            "INSERT INTO resources VALUES (?, ?, ?, ?, ?)",
            (str(resource.group.group_id), str(resource.resource_id),
             resource_name,
             str(resource.resource_category.resource_category_id),
             1 if resource.public else 0))
        __assign_resource_owner_role__(cursor, resource, user)

    return resource

def resource_category_by_id(
        conn: db.DbConnection, category_id: UUID) -> ResourceCategory:
    """Retrieve a resource category by its ID."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            "SELECT * FROM resource_categories WHERE "
            "resource_category_id=?",
            (str(category_id),))
        results = cursor.fetchone()
        if results:
            return ResourceCategory(
                UUID(results["resource_category_id"]),
                results["resource_category_key"],
                results["resource_category_description"])

    raise NotFoundError(
        f"Could not find a ResourceCategory with ID '{category_id}'")

def resource_categories(conn: db.DbConnection) -> Sequence[ResourceCategory]:
    """Retrieve all available resource categories"""
    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM resource_categories")
        return tuple(
            ResourceCategory(UUID(row[0]), row[1], row[2])
            for row in cursor.fetchall())
    return tuple()

def public_resources(conn: db.DbConnection) -> Sequence[Resource]:
    """List all resources marked as public"""
    categories = {
        str(cat.resource_category_id): cat for cat in resource_categories(conn)
    }
    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM resources WHERE public=1")
        results = cursor.fetchall()
        group_uuids = tuple(row[0] for row in results)
        query = ("SELECT * FROM groups WHERE group_id IN "
                 f"({', '.join(['?'] * len(group_uuids))})")
        cursor.execute(query, group_uuids)
        groups = {
            row[0]: Group(
                UUID(row[0]), row[1], json.loads(row[2] or "{}"))
            for row in cursor.fetchall()
        }
        return tuple(
            Resource(groups[row[0]], UUID(row[1]), row[2], categories[row[3]],
                     bool(row[4]))
            for row in results)

def group_leader_resources(
        cursor: db.DbCursor, user: User, group: Group,
        res_categories: Dict[UUID, ResourceCategory]) -> Sequence[Resource]:
    """Return all the resources available to the group leader"""
    if is_group_leader(cursor, user, group):
        cursor.execute("SELECT * FROM resources WHERE group_id=?",
                       (str(group.group_id),))
        return tuple(
            Resource(group, UUID(row[1]), row[2], res_categories[UUID(row[3])],
                     bool(row[4]))
            for row in cursor.fetchall())
    return tuple()

def user_resources(conn: db.DbConnection, user: User) -> Sequence[Resource]:
    """List the resources available to the user"""
    categories = { # Repeated in `public_resources` function
        cat.resource_category_id: cat for cat in resource_categories(conn)
    }
    with db.cursor(conn) as cursor:
        def __all_resources__(group) -> Sequence[Resource]:
            gl_resources = group_leader_resources(cursor, user, group, categories)

            cursor.execute(
                ("SELECT resources.* FROM group_user_roles_on_resources "
                 "LEFT JOIN resources "
                 "ON group_user_roles_on_resources.resource_id=resources.resource_id "
                 "WHERE group_user_roles_on_resources.group_id = ? "
                 "AND group_user_roles_on_resources.user_id = ?"),
                (str(group.group_id), str(user.user_id)))
            rows = cursor.fetchall()
            private_res = tuple(
                Resource(group, UUID(row[1]), row[2], categories[UUID(row[3])],
                         bool(row[4]))
                for row in rows)
            return tuple({
                res.resource_id: res
                for res in
                (private_res + gl_resources + public_resources(conn))# type: ignore[operator]
            }.values())

        # Fix the typing here
        return user_group(cursor, user).map(__all_resources__).maybe(# type: ignore[arg-type,misc]
            public_resources(conn), lambda res: res)# type: ignore[arg-type,return-value]

def attach_resource_data(cursor: db.DbCursor, resource: Resource) -> Resource:
    """Attach the linked data to the resource"""
    resource_data_function = {
        "mrna": mrna_resource_data,
        "genotype": genotype_resource_data,
        "phenotype": phenotype_resource_data
    }
    category = resource.resource_category
    data_rows = tuple(
        dict(data_row) for data_row in
        resource_data_function[category.resource_category_key](
            cursor, resource.resource_id))
    return Resource(
        resource.group, resource.resource_id, resource.resource_name,
        resource.resource_category, resource.public, data_rows)

def mrna_resource_data(
        cursor: db.DbCursor, resource_id: UUID) -> Sequence[sqlite3.Row]:
    """Fetch data linked to a mRNA resource"""
    cursor.execute(
        "SELECT * FROM mrna_resources AS mr INNER JOIN linked_group_data AS lgd"
        " ON (mr.dataset_id=lgd.dataset_or_trait_id "
        "AND mr.dataset_type=lgd.dataset_type) "
        "WHERE mr.resource_id=?",
        (str(resource_id),))
    return cursor.fetchall()

def genotype_resource_data(
        cursor: db.DbCursor, resource_id: UUID) -> Sequence[sqlite3.Row]:
    """Fetch data linked to a Genotype resource"""
    cursor.execute(
        "SELECT * FROM genotype_resources AS gr "
        "INNER JOIN linked_group_data AS lgd "
        "ON (gr.trait_id=lgd.dataset_or_trait_id "
        "AND gr.dataset_type=lgd.dataset_type) "
        "WHERE gr.resource_id=?",
        (str(resource_id),))
    return cursor.fetchall()

def phenotype_resource_data(
        cursor: db.DbCursor, resource_id: UUID) -> Sequence[sqlite3.Row]:
    """Fetch data linked to a Phenotype resource"""
    cursor.execute(
        "SELECT * FROM phenotype_resources AS pr "
        "INNER JOIN linked_group_data AS lgd "
        "ON (pr.trait_id=lgd.dataset_or_trait_id "
        "AND pr.dataset_type=lgd.dataset_type) "
        "WHERE pr.resource_id=?",
        (str(resource_id),))
    return cursor.fetchall()

def resource_by_id(
        conn: db.DbConnection, user: User, resource_id: UUID) -> Resource:
    """Retrieve a resource by its ID."""
    if not authorised_for(
            conn, user, ("group:resource:view-resource",),
            (resource_id,))[resource_id]:
        raise AuthorisationError(
            "You are not authorised to access resource with id "
            f"'{resource_id}'.")

    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM resources WHERE resource_id=:id",
                       {"id": str(resource_id)})
        row = cursor.fetchone()
        if row:
            return attach_resource_data(cursor, Resource(
                group_by_id(conn, UUID(row["group_id"])),
                UUID(row["resource_id"]), row["resource_name"],
                resource_category_by_id(conn, row["resource_category_id"]),
                bool(int(row["public"]))))

    raise NotFoundError(f"Could not find a resource with id '{resource_id}'")

def __link_mrna_data_to_resource__(
        conn: db.DbConnection, resource: Resource, dataset_id: str) -> dict:
    """Link mRNA Assay data with a resource."""
    with db.cursor(conn) as cursor:
        params = {
            "group_id": str(resource.group.group_id),
            "resource_id": str(resource.resource_id),
            "dataset_type": "mRNA",
            "dataset_id": dataset_id
        }
        cursor.execute(
            "INSERT INTO mrna_resources VALUES"
            "(:group_id, :resource_id, :dataset_type, :dataset_id)",
            params)
        return params

def __link_geno_data_to_resource__(
        conn: db.DbConnection, resource: Resource, dataset_id: str) -> dict:
    """Link Genotype data with a resource."""
    with db.cursor(conn) as cursor:
        params = {
            "group_id": str(resource.group.group_id),
            "resource_id": str(resource.resource_id),
            "dataset_type": "Genotype",
            "trait_id": dataset_id
        }
        cursor.execute(
            "INSERT INTO genotype_resources VALUES"
            "(:group_id, :resource_id, :dataset_type, :trait_id)",
            params)
        return params

def __link_pheno_data_to_resource__(
        conn: db.DbConnection, resource: Resource, dataset_id: str) -> dict:
    """Link Phenotype data with a resource."""
    with db.cursor(conn) as cursor:
        params = {
            "group_id": str(resource.group.group_id),
            "resource_id": str(resource.resource_id),
            "dataset_type": "Phenotype",
            "trait_id": dataset_id
        }
        cursor.execute(
            "INSERT INTO phenotype_resources VALUES"
            "(:group_id, :resource_id, :dataset_type, :trait_id)",
            params)
        return params

def link_data_to_resource(
        conn: db.DbConnection, user: User, resource_id: UUID, dataset_type: str,
        dataset_id: str):
    """Link data to resource."""
    resource = with_db_connection(partial(
        resource_by_id, user=user, resource_id=resource_id))
    return {
        "mrna": __link_mrna_data_to_resource__,
        "genotype": __link_geno_data_to_resource__,
        "phenotype": __link_pheno_data_to_resource__,
    }[dataset_type.lower()](conn, resource, dataset_id)
