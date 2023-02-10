"""
System admin privileges for data distribution

These privileges are focussed on allowing the system administrator to link the
datasets and traits in the main database to specific groups in the auth system.
"""

from yoyo import step

__depends__ = {'20230207_01_r0bkZ-create-group-join-requests-table'}

steps = [
    step(
        """
        INSERT INTO privileges VALUES
          ('system:data:link-to-group', 'Link a dataset or trait to a group.')
        """,
        """
        DELETE FROM privileges WHERE privilege_id IN
         ('system:data:link-to-group')
        """)
]
