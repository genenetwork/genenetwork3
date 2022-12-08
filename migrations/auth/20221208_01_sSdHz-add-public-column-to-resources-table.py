"""
Add 'public' column to 'resources' table
"""

from yoyo import step

__depends__ = {'20221206_01_BbeF9-create-group-user-roles-on-resources-table'}

steps = [
    step(
        """
        ALTER TABLE resources ADD COLUMN
            public INTEGER NOT NULL DEFAULT 0 CHECK (public=0 or public=1)
        """,
        "ALTER TABLE resources DROP COLUMN public")
]
