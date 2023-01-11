"""
remove 'create-group' privilege from group-leader.
"""

from yoyo import step

__depends__ = {'20221219_03_PcTrb-create-authorisation-code-table'}

steps = [
    step(
        """
        DELETE FROM role_privileges
        WHERE role_id='a0e67630-d502-4b9f-b23f-6805d0f30e30'
        AND privilege_id='4842e2aa-38b9-4349-805e-0a99a9cf8bff'
        """,
        """
        INSERT INTO role_privileges VALUES
        ('a0e67630-d502-4b9f-b23f-6805d0f30e30',
        '4842e2aa-38b9-4349-805e-0a99a9cf8bff')
        """),
    step(
        """
        INSERT INTO roles(role_id, role_name, user_editable) VALUES
          ('ade7e6b0-ba9c-4b51-87d0-2af7fe39a347', 'group-creator', '0')
        """,
        """
        DELETE FROM roles WHERE role_id='ade7e6b0-ba9c-4b51-87d0-2af7fe39a347'
        """),
    step(
        """
        INSERT INTO role_privileges VALUES
          ('ade7e6b0-ba9c-4b51-87d0-2af7fe39a347',
           '4842e2aa-38b9-4349-805e-0a99a9cf8bff')
        """,
        """
        DELETE FROM role_privileges
        WHERE role_id='ade7e6b0-ba9c-4b51-87d0-2af7fe39a347'
        AND privilege_id='4842e2aa-38b9-4349-805e-0a99a9cf8bff'
        """)
]
