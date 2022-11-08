"""Main entry point for project"""

from gn3.app import create_app

app = create_app()

##### BEGIN: CLI Commands #####

@app.cli.command()
def apply_migrations():
    from yoyo import get_backend, read_migrations
    from gn3.migrations import apply_migrations
    apply_migrations(
        get_backend(f'sqlite:///{app.config["AUTH_DB"]}'),
        read_migrations(app.config["AUTH_MIGRATIONS"]))

##### END: CLI Commands #####

if __name__ == '__main__':
    print("Starting app...")
    app.run()
