"""
create authorisation_code table
"""

from yoyo import step

__depends__ = {'20221219_02_buSEU-create-oauth2-tokens-table'}

steps = [
    step(
        """
        CREATE TABLE authorisation_code (
            code_id TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            client_id NOT NULL,
            redirect_uri TEXT,
            scope TEXT,
            nonce TEXT,
            auth_time INTEGER NOT NULL,
            code_challenge TEXT,
            code_challenge_method TEXT,
            user_id TEXT NOT NULL,
            PRIMARY KEY (code_id),
            FOREIGN KEY (client_id) REFERENCES oauth2_clients(client_id)
              ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
              ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS authorisation_code")
]
