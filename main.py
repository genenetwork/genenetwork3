"""Main entry point for project"""
from yoyo import get_backend, read_migrations

from gn3 import migrations
from gn3.app import create_app

app = create_app()

##### BEGIN: CLI Commands #####

@app.cli.command()
def apply_migrations():
    """Apply the dabasase migrations."""
    migrations.apply_migrations(
        get_backend(f'sqlite:///{app.config["AUTH_DB"]}'),
        read_migrations(app.config["AUTH_MIGRATIONS"]))

##### END: CLI Commands #####

if __name__ == '__main__':
    print("Starting app...")
    app.run()
