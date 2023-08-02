"""
Migrate existing data that is not assigned to any group to the default sys-admin
group for accessibility purposes.
"""
import sys
import json
import time
import random
from pathlib import Path
from uuid import UUID, uuid4

import click
from MySQLdb.cursors import DictCursor

from gn3 import db_utils as biodb

from gn3.auth import db as authdb
from gn3.auth.authentication.users import User
from gn3.auth.authorisation.groups.models import Group, save_group
from gn3.auth.roles.models import (
    revoke_user_role_by_name, assign_user_role_by_name)
from gn3.auth.authorisation.resources.models import (
    Resource, ResourceCategory, __assign_resource_owner_role__)

class DataNotFound(Exception):
    """Raise if no admin user exists."""

def sys_admins(conn: authdb.DbConnection) -> tuple[User, ...]:
    """Retrieve all the existing system admins."""
    with authdb.cursor(conn) as cursor:
        cursor.execute(
            "SELECT u.* FROM users AS u "
            "INNER JOIN user_roles AS ur ON u.user_id=ur.user_id "
            "INNER JOIN roles AS r ON ur.role_id=r.role_id "
            "WHERE r.role_name='system-administrator'")
        return tuple(User(UUID(row["user_id"]), row["email"], row["name"])
                     for row in cursor.fetchall())
    return tuple()

def choose_admin(enum_admins: dict[int, User]) -> int:
    """Prompt and read user choice."""
    while True:
        try:
            print("\n===========================\n")
            print("We found the following system administrators:")
            for idx, admin in enum_admins.items():
                print(f"\t{idx}: {admin.name} ({admin.email})")
            choice = input(f"Choose [1 .. {len(enum_admins)}]: ")
            return int(choice)
        except ValueError as _verr:
            if choice.lower() == "quit":
                print("Goodbye!")
                sys.exit(0)
            print(f"\nERROR: Invalid choice '{choice}'!")

def select_sys_admin(admins: tuple[User, ...]) -> User:
    """Pick one admin out of list."""
    if len(admins) > 0:
        if len(admins) == 1:
            print(f"-> Found Admin: {admins[0].name} ({admins[0].email})")
            return admins[0]
        enum_admins = dict(enumerate(admins, start=1))
        chosen = enum_admins[choose_admin(enum_admins)]
        print(f"-> Chosen Admin: {chosen.name} ({chosen.email})")
        return chosen
    raise DataNotFound(
        "No administrator user found. Create an administrator user first.")

def admin_group(conn: authdb.DbConnection, admin: User) -> Group:
    """Retrieve the admin's user group. If none exist, create one."""
    with authdb.cursor(conn) as cursor:
        cursor.execute(
            "SELECT g.* FROM users AS u "
            "INNER JOIN group_users AS gu ON u.user_id=gu.user_id "
            "INNER JOIN groups AS g on gu.group_id=g.group_id "
            "WHERE u.user_id = ?",
            (str(admin.user_id),))
        row = cursor.fetchone()
        if row:
            return Group(UUID(row["group_id"]),
                         row["group_name"],
                         json.loads(row["group_metadata"]))
        new_group = save_group(cursor, "AutoAdminGroup", {
            "group_description": (
                "Created by script for existing data visibility. "
                "Existing data was migrated into this group and assigned "
                "to publicly visible resources according to type.")
        })
        cursor.execute("INSERT INTO group_users VALUES (?, ?)",
                       (str(new_group.group_id), str(admin.user_id)))
        revoke_user_role_by_name(cursor, group_leader, "group-creator")
        assign_user_role_by_name(cursor, group_leader, "group-leader")
        return new_group

def __resource_category_by_key__(
        cursor: authdb.DbCursor, category_key: str) -> ResourceCategory:
    """Retrieve a resource category by its ID."""
    cursor.execute(
        "SELECT * FROM resource_categories WHERE resource_category_key = ?",
        (category_key,))
    row = cursor.fetchone()
    if not bool(row):
        raise DataNotFound(
            f"Could not find resource category with key {category_key}")
    return ResourceCategory(UUID(row["resource_category_id"]),
                            row["resource_category_key"],
                            row["resource_category_description"])

def __create_resources__(cursor: authdb.DbCursor, group: Group) -> tuple[
        Resource, ...]:
    """Create default resources."""
    resources = tuple(Resource(
        group, uuid4(), name, __resource_category_by_key__(cursor, catkey),
        True, tuple()
    ) for name, catkey in (
        ("mRNA-euhrin", "mrna"),
        ("pheno-xboecp", "phenotype"),
        ("geno-welphd", "genotype")))
    cursor.executemany(
        "INSERT INTO resources VALUES (:gid, :rid, :rname, :rcid, :pub)",
        tuple({
            "gid": str(group.group_id),
            "rid": str(res.resource_id),
            "rname": res.resource_name,
            "rcid": str(res.resource_category.resource_category_id),
            "pub": 1
        } for res in resources))
    return resources

def default_resources(conn: authdb.DbConnection, group: Group) -> tuple[
        Resource, ...]:
    """Create default resources, or return them if they exist."""
    with authdb.cursor(conn) as cursor:
        cursor.execute(
            "SELECT r.resource_id, r.resource_name, r.public, rc.* "
            "FROM resources AS r INNER JOIN resource_categories AS rc "
            "ON r.resource_category_id=rc.resource_category_id "
            "WHERE r.group_id=? AND r.resource_name IN "
            "('mRNA-euhrin', 'pheno-xboecp', 'geno-welphd')",
            (str(group.group_id),))
        rows = cursor.fetchall()
        if len(rows) == 0:
            return __create_resources__(cursor, group)

        return tuple(Resource(
            group,
            UUID(row["resource_id"]),
            row["resource_name"],
            ResourceCategory(
                UUID(row["resource_category_id"]),
                row["resource_category_key"],
                row["resource_category_description"]),
            bool(row["public"]),
            tuple()
        ) for row in rows)

def delay():
    """Delay a while: anything from 2 seconds to 15 seconds."""
    time.sleep(random.choice(range(2,16)))

def __assigned_mrna__(authconn):
    """Retrieve assigned mRNA items."""
    with authdb.cursor(authconn) as cursor:
        cursor.execute(
            "SELECT SpeciesId, InbredSetId, ProbeFreezeId, ProbeSetFreezeId "
            "FROM linked_mrna_data")
        return tuple(
            (row["SpeciesId"], row["InbredSetId"], row["ProbeFreezeId"],
             row["ProbeSetFreezeId"]) for row in cursor.fetchall())

def __unassigned_mrna__(bioconn, assigned):
    """Retrieve unassigned mRNA data items."""
    query = (
        "SELECT s.SpeciesId, iset.InbredSetId, pf.ProbeFreezeId, "
        "psf.Id AS ProbeSetFreezeId, psf.Name AS dataset_name, "
        "psf.FullName AS dataset_fullname, psf.ShortName AS dataset_shortname "
        "FROM Species AS s INNER JOIN InbredSet AS iset "
        "ON s.SpeciesId=iset.SpeciesId INNER JOIN ProbeFreeze AS pf "
        "ON iset.InbredSetId=pf.InbredSetId INNER JOIN ProbeSetFreeze AS psf "
        "ON pf.ProbeFreezeId=psf.ProbeFreezeId ")
    if len(assigned) > 0:
        paramstr = ", ".join(["(%s, %s, %s, %s)"] * len(assigned))
        query = query + (
            "WHERE (s.SpeciesId, iset.InbredSetId, pf.ProbeFreezeId, psf.Id) "
            f"NOT IN ({paramstr}) ")

    query = query + "LIMIT 100000"
    with bioconn.cursor(DictCursor) as cursor:
        cursor.execute(query, tuple(item for row in assigned for item in row))
        return (row for row in cursor.fetchall())

def __assign_mrna__(authconn, bioconn, resource):
    "Assign any unassigned mRNA data to resource."
    while True:
        unassigned = tuple({
            "data_link_id": str(uuid4()),
            "group_id": str(resource.group.group_id),
            "resource_id": str(resource.resource_id),
            **row
        } for row in __unassigned_mrna__(
            bioconn, __assigned_mrna__(authconn)))

        if len(unassigned) <= 0:
            print("-> mRNA: Completed!")
            break
        with authdb.cursor(authconn) as cursor:
            cursor.executemany(
                "INSERT INTO linked_mrna_data VALUES "
                "(:data_link_id, :group_id, :SpeciesId, :InbredSetId, "
                ":ProbeFreezeId, :ProbeSetFreezeId, :dataset_name, "
                ":dataset_fullname, :dataset_shortname)",
                unassigned)
            cursor.executemany(
                "INSERT INTO mrna_resources VALUES "
                "(:group_id, :resource_id, :data_link_id)",
                unassigned)
            print(f"-> mRNA: Linked {len(unassigned)}")
            delay()

def __assigned_geno__(authconn):
    """Retrieve assigned genotype data."""
    with authdb.cursor(authconn) as cursor:
        cursor.execute(
            "SELECT SpeciesId, InbredSetId, GenoFreezeId "
            "FROM linked_genotype_data")
        return tuple((row["SpeciesId"], row["InbredSetId"], row["GenoFreezeId"])
                     for row in cursor.fetchall())

def __unassigned_geno__(bioconn, assigned):
    """Fetch unassigned genotype data."""
    query = (
        "SELECT s.SpeciesId, iset.InbredSetId, iset.InbredSetName, "
        "gf.Id AS GenoFreezeId, gf.Name AS dataset_name, "
        "gf.FullName AS dataset_fullname, "
        "gf.ShortName AS dataset_shortname "
        "FROM Species AS s INNER JOIN InbredSet AS iset "
        "ON s.SpeciesId=iset.SpeciesId INNER JOIN GenoFreeze AS gf "
        "ON iset.InbredSetId=gf.InbredSetId ")
    if len(assigned) > 0:
        paramstr = ", ".join(["(%s, %s, %s)"] * len(assigned))
        query = query + (
            "WHERE (s.SpeciesId, iset.InbredSetId, gf.Id) "
            f"NOT IN ({paramstr}) ")

    query = query + "LIMIT 100000"
    with bioconn.cursor(DictCursor) as cursor:
        cursor.execute(query, tuple(item for row in assigned for item in row))
        return (row for row in cursor.fetchall())

def __assign_geno__(authconn, bioconn, resource):
    "Assign any unassigned Genotype data to resource."
    while True:
        unassigned = tuple({
            "data_link_id": str(uuid4()),
            "group_id": str(resource.group.group_id),
            "resource_id": str(resource.resource_id),
            **row
        } for row in __unassigned_geno__(
            bioconn, __assigned_geno__(authconn)))

        if len(unassigned) <= 0:
            print("-> Genotype: Completed!")
            break
        with authdb.cursor(authconn) as cursor:
            cursor.executemany(
                "INSERT INTO linked_genotype_data VALUES "
                "(:data_link_id, :group_id, :SpeciesId, :InbredSetId, "
                ":GenoFreezeId, :dataset_name, :dataset_fullname, "
                ":dataset_shortname)",
                unassigned)
            cursor.executemany(
                "INSERT INTO genotype_resources VALUES "
                "(:group_id, :resource_id, :data_link_id)",
                unassigned)
            print(f"-> Genotype: Linked {len(unassigned)}")
            delay()

def __assigned_pheno__(authconn):
    """Retrieve assigned phenotype data."""
    with authdb.cursor(authconn) as cursor:
        cursor.execute(
            "SELECT SpeciesId, InbredSetId, PublishFreezeId, PublishXRefId "
            "FROM linked_phenotype_data")
        return tuple((
            row["SpeciesId"], row["InbredSetId"], row["PublishFreezeId"],
            row["PublishXRefId"]) for row in cursor.fetchall())

def __unassigned_pheno__(bioconn, assigned):
    """Retrieve all unassigned Phenotype data."""
    query = (
            "SELECT spc.SpeciesId, iset.InbredSetId, "
            "pf.Id AS PublishFreezeId, pf.Name AS dataset_name, "
            "pf.FullName AS dataset_fullname, "
            "pf.ShortName AS dataset_shortname, pxr.Id AS PublishXRefId "
            "FROM "
            "Species AS spc "
            "INNER JOIN InbredSet AS iset "
            "ON spc.SpeciesId=iset.SpeciesId "
            "INNER JOIN PublishFreeze AS pf "
            "ON iset.InbredSetId=pf.InbredSetId "
            "INNER JOIN PublishXRef AS pxr "
            "ON pf.InbredSetId=pxr.InbredSetId ")
    if len(assigned) > 0:
        paramstr = ", ".join(["(%s, %s, %s, %s)"] * len(assigned))
        query = query + (
            "WHERE (spc.SpeciesId, iset.InbredSetId, pf.Id, pxr.Id) "
            f"NOT IN ({paramstr}) ")

    query = query + "LIMIT 100000"
    with bioconn.cursor(DictCursor) as cursor:
        cursor.execute(query, tuple(item for row in assigned for item in row))
        return (row for row in cursor.fetchall())

def __assign_pheno__(authconn, bioconn, resource):
    """Assign any unassigned Phenotype data to resource."""
    while True:
        unassigned = tuple({
            "data_link_id": str(uuid4()),
            "group_id": str(resource.group.group_id),
            "resource_id": str(resource.resource_id),
            **row
        } for row in __unassigned_pheno__(
            bioconn, __assigned_pheno__(authconn)))

        if len(unassigned) <= 0:
            print("-> Phenotype: Completed!")
            break
        with authdb.cursor(authconn) as cursor:
            cursor.executemany(
                "INSERT INTO linked_phenotype_data VALUES "
                "(:data_link_id, :group_id, :SpeciesId, :InbredSetId, "
                ":PublishFreezeId, :dataset_name, :dataset_fullname, "
                ":dataset_shortname, :PublishXRefId)",
                unassigned)
            cursor.executemany(
                "INSERT INTO phenotype_resources VALUES "
                "(:group_id, :resource_id, :data_link_id)",
                unassigned)
            print(f"-> Phenotype: Linked {len(unassigned)}")
            delay()

def assign_data_to_resource(authconn, bioconn, resource: Resource):
    """Assign existing data, not linked to any group to the resource."""
    assigner_fns = {
        "mrna": __assign_mrna__,
        "genotype": __assign_geno__,
        "phenotype": __assign_pheno__
    }
    return assigner_fns[resource.resource_category.resource_category_key](
        authconn, bioconn, resource)

def entry(authdbpath, mysqldburi):
    """Entry-point for data migration."""
    if not Path(authdbpath).exists():
        print(
            f"ERROR: Auth db file `{authdbpath}` does not exist.",
            file=sys.stderr)
        sys.exit(2)
    try:
        with (authdb.connection(authdbpath) as authconn,
              biodb.database_connection(mysqldburi) as bioconn):
            admin = select_sys_admin(sys_admins(authconn))
            resources = default_resources(
                authconn, admin_group(authconn, admin))
            for resource in resources:
                assign_data_to_resource(authconn, bioconn, resource)
                with authdb.cursor(authconn) as cursor:
                    __assign_resource_owner_role__(cursor, resource, admin)
    except DataNotFound as dnf:
        print(dnf.args[0], file=sys.stderr)
        sys.exit(1)

@click.command()
@click.argument("authdbpath") # "Path to the Auth(entic|oris)ation database"
@click.argument("mysqldburi") # "URI to the MySQL database with the biology data"
def run(authdbpath, mysqldburi):
    """Setup command-line arguments."""
    entry(authdbpath, mysqldburi)

if __name__ == "__main__":
    run() # pylint: disable=[no-value-for-parameter]
