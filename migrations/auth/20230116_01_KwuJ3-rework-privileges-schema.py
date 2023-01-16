"""
rework privileges schema
"""
import contextlib

from yoyo import step

__depends__ = {'20230111_01_Wd6IZ-remove-create-group-privilege-from-group-leader'}

privileges = ( # format: (original_id, original_name, new_id, category)
    ("13ec2a94-4f1a-442d-aad2-936ad6dd5c57", "delete-group",
     "system:group:delete-group", "group-management"),
    ("1c59eff5-9336-4ed2-a166-8f70d4cb012e", "delete-role",
     "group:role:delete-role", "role-management"),
    ("1fe61370-cae9-4983-bd6c-ce61050c510f", "delete-any-user",
     "system:user:delete-user", "user-management"),
    ("221660b1-df05-4be1-b639-f010269dbda9", "create-role",
     "group:role:create-role", "role-management"),
    ("2f980855-959b-4339-b80e-25d1ec286e21", "edit-resource",
     "group:resource:edit-resource", "resource-management"),
    ("3ebfe79c-d159-4629-8b38-772cf4bc2261", "view-group",
     "system:group:view-group", "group-management"),
    ("4842e2aa-38b9-4349-805e-0a99a9cf8bff", "create-group",
     "system:group:create-group", "group-management"),
    ("5103cc68-96f8-4ebb-83a4-a31692402c9b", "assign-role",
     "group:user:assign-role", "role-management"),
    ("519db546-d44e-4fdc-9e4e-25aa67548ab3", "masquerade",
     "system:user:masquerade", "system-admin"),
    ("52576370-b3c7-4e6a-9f7e-90e9dbe24d8f", "edit-group",
     "system:group:edit-group", "group-management"),
    ("7bcca363-cba9-4169-9e31-26bdc6179b28", "edit-role",
     "group:role:edit-role", "role-management"),
    ("7f261757-3211-4f28-a43f-a09b800b164d", "view-resource",
     "group:resource:view-resource", "resource-management"),
    ("80f11285-5079-4ec0-907c-06509f88a364", "assign-group-leader",
     "system:user:assign-group-leader", "group-management"),
    ("aa25b32a-bff2-418d-b0a2-e26b4a8f089b", "create-resource",
     "group:resource:create-resource", "resource-management"),
    ("ae4add8c-789a-4d11-a6e9-a306470d83d9", "add-group-member",
     "group:user:add-group-member", "group-management"),
    ("d2a070fd-e031-42fb-ba41-d60cf19e5d6d", "delete-resource",
     "group:resource:delete-resource", "resource-management"),
    ("d4afe2b3-4ca0-4edd-b37d-966535b5e5bd", "transfer-group-leadership",
     "system:group:transfer-group-leader", "group-management"),
    ("e7252301-6ee0-43ba-93ef-73b607cf06f6", "reset-any-password",
     "system:user:reset-password", "user-management"),
    ("f1bd3f42-567e-4965-9643-6d1a52ddee64", "remove-group-member",
     "group:user:remove-group-member", "group-management"))

def rework_privileges_table(cursor):
    "rework the schema"
    cursor.executemany(
        ("UPDATE privileges SET privilege_id=:id "
         "WHERE privilege_id=:old_id"),
        ({"id": row[2], "old_id": row[0]} for row in privileges))
    cursor.execute("ALTER TABLE privileges DROP COLUMN privilege_category")
    cursor.execute("ALTER TABLE privileges DROP COLUMN privilege_name")

def restore_privileges_table(cursor):
    "restore the schema"
    cursor.execute((
        "CREATE TABLE privileges_restore ("
        "  privilege_id TEXT PRIMARY KEY,"
        "  privilege_name TEXT NOT NULL,"
        "  privilege_category TEXT NOT NULL DEFAULT 'common',"
        "  privilege_description TEXT"
        ")"))
    id_dict = {row[2]: {"id": row[0], "name": row[1], "cat": row[3]}
               for row in privileges}
    cursor.execute(
        "SELECT privilege_id, privilege_description FROM privileges")
    params = ({**id_dict[row[0]], "desc": row[1]} for row in cursor.fetchall())
    cursor.executemany(
        "INSERT INTO privileges_restore VALUES (:id, :name, :cat, :desc)",
        params)
    cursor.execute("DROP TABLE privileges")
    cursor.execute("ALTER TABLE privileges_restore RENAME TO privileges")

def update_privilege_ids_in_role_privileges(cursor):
    """Update the ids to new form."""
    cursor.executemany(
        ("UPDATE role_privileges SET privilege_id=:new_id "
         "WHERE privilege_id=:old_id"),
        ({"new_id": row[2], "old_id": row[0]} for row in privileges))

def restore_privilege_ids_in_role_privileges(cursor):
    """Restore original ids"""
    cursor.executemany(
        ("UPDATE role_privileges SET privilege_id=:old_id "
         "WHERE privilege_id=:new_id"),
        ({"new_id": row[2], "old_id": row[0]} for row in privileges))

def change_schema(conn):
    """Change the privileges schema and IDs"""
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute("PRAGMA foreign_keys=OFF")
        rework_privileges_table(cursor)
        update_privilege_ids_in_role_privileges(cursor)
        cursor.execute("PRAGMA foreign_keys=ON")

def restore_schema(conn):
    """Change the privileges schema and IDs"""
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute("PRAGMA foreign_keys=OFF")
        restore_privilege_ids_in_role_privileges(cursor)
        restore_privileges_table(cursor)
        cursor.execute("PRAGMA foreign_keys=ON")

steps = [
    step(change_schema, restore_schema)
]
