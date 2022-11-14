"""
Enumerate initial privileges
"""

from yoyo import step

__depends__ = {'20221110_08_23psB-add-privilege-category-and-privilege-description-columns-to-privileges-table'}

steps = [
    step(
        """
        INSERT INTO
            privileges(privilege_id, privilege_name, privilege_category,
                       privilege_description)
        VALUES
            -- group-management privileges
            ('4842e2aa-38b9-4349-805e-0a99a9cf8bff', 'create-group',
             'group-management', 'Create a group'),
            ('3ebfe79c-d159-4629-8b38-772cf4bc2261', 'view-group',
             'group-management', 'View the details of a group'),
            ('52576370-b3c7-4e6a-9f7e-90e9dbe24d8f', 'edit-group',
             'group-management', 'Edit the details of a group'),
            ('13ec2a94-4f1a-442d-aad2-936ad6dd5c57', 'delete-group',
             'group-management', 'Delete a group'),
            ('ae4add8c-789a-4d11-a6e9-a306470d83d9', 'add-group-member',
             'group-management', 'Add a user to a group'),
            ('f1bd3f42-567e-4965-9643-6d1a52ddee64', 'remove-group-member',
             'group-management', 'Remove a user from a group'),
            ('80f11285-5079-4ec0-907c-06509f88a364', 'assign-group-leader',
             'group-management', 'Assign user group-leader privileges'),
            ('d4afe2b3-4ca0-4edd-b37d-966535b5e5bd',
             'transfer-group-leadership', 'group-management',
             'Transfer leadership of the group to some other member'),

            -- resource-management privileges
            ('aa25b32a-bff2-418d-b0a2-e26b4a8f089b', 'create-resource',
             'resource-management', 'Create a resource object'),
            ('7f261757-3211-4f28-a43f-a09b800b164d', 'view-resource',
             'resource-management', 'view a resource and use it in computations'),
            ('2f980855-959b-4339-b80e-25d1ec286e21', 'edit-resource',
             'resource-management', 'edit/update a resource'),
            ('d2a070fd-e031-42fb-ba41-d60cf19e5d6d', 'delete-resource',
             'resource-management', 'Delete a resource'),

            -- role-management privileges
            ('221660b1-df05-4be1-b639-f010269dbda9', 'create-role',
             'role-management', 'Create a new role'),
            ('7bcca363-cba9-4169-9e31-26bdc6179b28', 'edit-role',
             'role-management', 'edit/update an existing role'),
            ('5103cc68-96f8-4ebb-83a4-a31692402c9b', 'assign-role',
             'role-management', 'Assign a role to an existing user'),
            ('1c59eff5-9336-4ed2-a166-8f70d4cb012e', 'delete-role',
             'role-management', 'Delete an existing role'),

            -- user-management privileges
            ('e7252301-6ee0-43ba-93ef-73b607cf06f6', 'reset-any-password',
             'user-management', 'Reset the password for any user'),
            ('1fe61370-cae9-4983-bd6c-ce61050c510f', 'delete-any-user',
             'user-management', 'Delete any user from the system'),

            -- sytem-admin privileges
            ('519db546-d44e-4fdc-9e4e-25aa67548ab3', 'masquerade',
             'system-admin', 'Masquerade as some other user')
        """,
        "DELETE FROM privileges")
]
