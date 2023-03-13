"""
create oauth2_tokens table
"""

from yoyo import step

__depends__ = {'20221219_01_CI3tN-create-oauth2-clients-table'}

steps = [
    step(
        """
        CREATE TABLE oauth2_tokens(
            token_id TEXT NOT NULL,
            client_id TEXT NOT NULL,
            token_type TEXT NOT NULL,
            access_token TEXT UNIQUE NOT NULL,
            refresh_token TEXT,
            scope TEXT,
            revoked INTEGER CHECK (revoked = 0 or revoked = 1),
            issued_at INTEGER NOT NULL,
            expires_in INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            PRIMARY KEY(token_id),
            FOREIGN KEY (client_id) REFERENCES oauth2_clients(client_id)
              ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
              ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS oauth2_tokens")
]
