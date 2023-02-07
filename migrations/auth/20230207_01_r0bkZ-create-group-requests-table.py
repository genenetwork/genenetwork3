"""
Create group_requests table
"""

from yoyo import step

__depends__ = {'20230116_01_KwuJ3-rework-privileges-schema'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS group_requests(
            request_id TEXT NOT NULL,
            group_id TEXT NOT NULL,
            requester_id TEXT NOT NULL,
            request_type TEXT NOT NULL,
            timestamp REAL NOT NULL,
            message TEXT,
            PRIMARY KEY(request_id, group_id),
            FOREIGN KEY(group_id) REFERENCES groups(group_id)
            ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (requester_id) REFERENCES users(user_id)
            ON UPDATE CASCADE ON DELETE CASCADE
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS group_requests")
]
