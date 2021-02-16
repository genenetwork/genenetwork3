"""Main entry point for project"""

from gn3.app import create_app


app = create_app()
app.run(host="0.0.0.0")
