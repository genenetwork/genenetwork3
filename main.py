"""Main entry point for project"""
import sys
import uuid
import json
from math import ceil
from datetime import datetime


import click
from yoyo import get_backend, read_migrations

from gn3 import migrations
from gn3.app import create_app
from gn3.auth.authentication.users import hash_password

from gn3.auth import db

from scripts import register_sys_admin as rsysadm# type: ignore[import]
from scripts import migrate_existing_data as med# type: ignore[import]

app = create_app()

##### BEGIN: CLI Commands #####

@app.cli.command()
def apply_migrations():
    """Apply the dabasase migrations."""
    migrations.apply_migrations(
        get_backend(f'sqlite:///{app.config["AUTH_DB"]}'),
        read_migrations(app.config["AUTH_MIGRATIONS"]))

def __init_dev_users__():
    """Initialise dev users. Get's used in more than one place"""
    dev_users_query = "INSERT INTO users VALUES (:user_id, :email, :name)"
    dev_users_passwd = "INSERT INTO user_credentials VALUES (:user_id, :hash)"
    dev_users = ({
        "user_id": "0ad1917c-57da-46dc-b79e-c81c91e5b928",
        "email": "test@development.user",
        "name": "Test Development User",
        "password": "testpasswd"},)

    with db.connection(app.config["AUTH_DB"]) as conn, db.cursor(conn) as cursor:
        cursor.executemany(dev_users_query, dev_users)
        cursor.executemany(dev_users_passwd, (
            {**usr, "hash": hash_password(usr["password"])}
            for usr in dev_users))

@app.cli.command()
def init_dev_users():
    """
    Initialise development users for OAuth2 sessions.

    **NOTE**: You really should not run this in production/staging
    """
    __init_dev_users__()

@app.cli.command()
def init_dev_clients():
    """
    Initialise a development client for OAuth2 sessions.

    **NOTE**: You really should not run this in production/staging
    """
    __init_dev_users__()
    dev_clients_query = (
        "INSERT INTO oauth2_clients VALUES ("
        ":client_id, :client_secret, :client_id_issued_at, "
        ":client_secret_expires_at, :client_metadata, :user_id"
        ")")
    dev_clients = ({
        "client_id": "0bbfca82-d73f-4bd4-a140-5ae7abb4a64d",
        "client_secret": "yadabadaboo",
        "client_id_issued_at": ceil(datetime.now().timestamp()),
        "client_secret_expires_at": 0,
        "client_metadata": json.dumps({
            "client_name": "GN2 Dev Server",
            "token_endpoint_auth_method": [
                "client_secret_post", "client_secret_basic"],
            "client_type": "confidential",
            "grant_types": ["password", "authorization_code", "refresh_token"],
            "default_redirect_uri": "http://localhost:5033/oauth2/code",
            "redirect_uris": ["http://localhost:5033/oauth2/code",
                              "http://localhost:5033/oauth2/token"],
            "response_type": ["code", "token"],
            "scope": ["profile", "group", "role", "resource", "register-client",
                      "user", "masquerade", "migrate-data", "introspect"]
        }),
        "user_id": "0ad1917c-57da-46dc-b79e-c81c91e5b928"},)

    with db.connection(app.config["AUTH_DB"]) as conn, db.cursor(conn) as cursor:
        cursor.executemany(dev_clients_query, dev_clients)


@app.cli.command()
@click.argument("user_id", type=click.UUID)
def assign_system_admin(user_id: uuid.UUID):
    """Assign user with ID `user_id` administrator role."""
    dburi = app.config["AUTH_DB"]
    with db.connection(dburi) as conn, db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM users WHERE user_id=?",
                       (str(user_id),))
        row = cursor.fetchone()
        if row:
            cursor.execute(
                "SELECT * FROM roles WHERE role_name='system-administrator'")
            admin_role = cursor.fetchone()
            cursor.execute("INSERT INTO user_roles VALUES (?,?)",
                           (str(user_id), admin_role["role_id"]))
            return 0
        print(f"ERROR: Could not find user with ID {user_id}",
              file=sys.stderr)
        sys.exit(1)

@app.cli.command()
def make_data_public():
    """Make existing data that is not assigned to any group publicly visible."""
    med.entry(app.config["AUTH_DB"], app.config["SQL_URI"])

@app.cli.command()
def register_admin():
    """Register the administrator."""
    rsysadm.register_admin(app.config["AUTH_DB"])

##### END: CLI Commands #####

if __name__ == '__main__':
    print("Starting app...")
    app.run()
