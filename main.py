"""Main entry point for project"""
import json
from math import ceil
from datetime import datetime

import bcrypt
from yoyo import get_backend, read_migrations

from gn3 import migrations
from gn3.app import create_app

from gn3.auth import db

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
        "email": "test@develpment.user",
        "name": "Test Development User",
        "password": "testpasswd"},)

    def __hash_passwd__(passwd):
        return bcrypt.hashpw(passwd.encode("utf8"), bcrypt.gensalt())

    with db.connection(app.config["AUTH_DB"]) as conn, db.cursor(conn) as cursor:
        cursor.executemany(dev_users_query, dev_users)
        cursor.executemany(dev_users_passwd, (
            {**usr, "hash": __hash_passwd__(usr["password"])}
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
            "grant_types": ["password", "authorisation_code", "refresh_token"],
            "default_redirect_uri": "http://localhost:5033/oauth2/code",
            "redirect_uris": ["http://localhost:5033/oauth2/code"],
            "response_type": "token", # choices: ["code", "token"]
            "scope": ["profile", "resource", "register-client"]
        }),
        "user_id": "0ad1917c-57da-46dc-b79e-c81c91e5b928"},)

    with db.connection(app.config["AUTH_DB"]) as conn, db.cursor(conn) as cursor:
        cursor.executemany(dev_clients_query, dev_clients)

##### END: CLI Commands #####

if __name__ == '__main__':
    print("Starting app...")
    app.run()
