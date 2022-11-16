"""
Add privileges to 'group-leader' role.
"""

from yoyo import step

__depends__ = {'20221114_05_hQun6-create-user-roles-table'}

steps = [
    step(
        """
        INSERT INTO role_privileges(role_id, privilege_id)
        VALUES
            -- role management
            ('a0e67630-d502-4b9f-b23f-6805d0f30e30',
             '221660b1-df05-4be1-b639-f010269dbda9'),
            ('a0e67630-d502-4b9f-b23f-6805d0f30e30',
             '7bcca363-cba9-4169-9e31-26bdc6179b28'),
            ('a0e67630-d502-4b9f-b23f-6805d0f30e30',
             '5103cc68-96f8-4ebb-83a4-a31692402c9b'),
            ('a0e67630-d502-4b9f-b23f-6805d0f30e30',
             '1c59eff5-9336-4ed2-a166-8f70d4cb012e')
        """,
        """
        DELETE FROM role_privileges
        WHERE
            role_id='a0e67630-d502-4b9f-b23f-6805d0f30e30'
        AND privilege_id IN (
            '221660b1-df05-4be1-b639-f010269dbda9',
            '7bcca363-cba9-4169-9e31-26bdc6179b28',
            '5103cc68-96f8-4ebb-83a4-a31692402c9b',
            '1c59eff5-9336-4ed2-a166-8f70d4cb012e'
        )
        """)
]
