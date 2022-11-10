"""Run the migrations in the app, rather than with yoyo CLI."""
from pathlib import Path
from typing import Union

from yoyo import read_migrations
from yoyo.backends import DatabaseBackend
from yoyo.migrations import Migration, MigrationList

class MigrationNotFound(Exception):
    """Raised if a migration is not found at the given path."""
    def __init__(self, migration_path: Path):
        """Initialise the exception."""
        super().__init__(f"Could not find migration '{migration_path}'")

def apply_migrations(backend: DatabaseBackend, migrations: MigrationList):
    "Apply the provided migrations."
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))

def rollback_migrations(backend: DatabaseBackend, migrations: MigrationList):
    "Rollback the provided migrations."
    with backend.lock():
        backend.rollback_migrations(backend.to_rollback(migrations))

def get_migration(migration_path: Union[Path, str]) -> Migration:
    """Retrieve a migration at thi given `migration_path`."""
    migration_path = Path(migration_path)
    if migration_path.exists():
        for migration in read_migrations(str(migration_path.parent)):
            if Path(migration.path) == migration_path:
                return migration

    raise MigrationNotFound(migration_path)
