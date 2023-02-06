"""
Initialise basic roles
"""

from yoyo import step

__depends__ = {'20221114_03_PtWjc-create-group-roles-table'}

steps = [
    step(
        """
        INSERT INTO roles(role_id, role_name, user_editable) VALUES
            ('a0e67630-d502-4b9f-b23f-6805d0f30e30', 'group-leader', '0'),
            ('522e4d40-aefc-4a64-b7e0-768b8be517ee', 'resource-owner', '0')
        """,
        "DELETE FROM roles"),
    step(
        """
        INSERT INTO role_privileges(role_id, privilege_id)
        VALUES
            -- group-management
            ('a0e67630-d502-4b9f-b23f-6805d0f30e30',
             '4842e2aa-38b9-4349-805e-0a99a9cf8bff'),
            ('a0e67630-d502-4b9f-b23f-6805d0f30e30',
             '3ebfe79c-d159-4629-8b38-772cf4bc2261'),
            ('a0e67630-d502-4b9f-b23f-6805d0f30e30',
             '52576370-b3c7-4e6a-9f7e-90e9dbe24d8f'),
            ('a0e67630-d502-4b9f-b23f-6805d0f30e30',
             '13ec2a94-4f1a-442d-aad2-936ad6dd5c57'),
            ('a0e67630-d502-4b9f-b23f-6805d0f30e30',
             'ae4add8c-789a-4d11-a6e9-a306470d83d9'),
            ('a0e67630-d502-4b9f-b23f-6805d0f30e30',
             'f1bd3f42-567e-4965-9643-6d1a52ddee64'),
            ('a0e67630-d502-4b9f-b23f-6805d0f30e30',
             'd4afe2b3-4ca0-4edd-b37d-966535b5e5bd'),

            -- resource-management
            ('a0e67630-d502-4b9f-b23f-6805d0f30e30',
             'aa25b32a-bff2-418d-b0a2-e26b4a8f089b'),
            ('a0e67630-d502-4b9f-b23f-6805d0f30e30',
             '7f261757-3211-4f28-a43f-a09b800b164d'),
            ('a0e67630-d502-4b9f-b23f-6805d0f30e30',
             '2f980855-959b-4339-b80e-25d1ec286e21'),
            ('a0e67630-d502-4b9f-b23f-6805d0f30e30',
             'd2a070fd-e031-42fb-ba41-d60cf19e5d6d'),
            ('522e4d40-aefc-4a64-b7e0-768b8be517ee',
             'aa25b32a-bff2-418d-b0a2-e26b4a8f089b'),
            ('522e4d40-aefc-4a64-b7e0-768b8be517ee',
             '7f261757-3211-4f28-a43f-a09b800b164d'),
            ('522e4d40-aefc-4a64-b7e0-768b8be517ee',
             '2f980855-959b-4339-b80e-25d1ec286e21'),
            ('522e4d40-aefc-4a64-b7e0-768b8be517ee',
             'd2a070fd-e031-42fb-ba41-d60cf19e5d6d')
        """,
        "DELETE FROM role_privileges")
]
