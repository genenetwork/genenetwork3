"""Main entry point for project"""

from gn3.app import create_app

app = create_app()

if __name__ == "__main__":
    print("Starting app...")
    app.run()
