"""Main entry point for project"""

from gn3.app import create_app
from gn3.api.gemma import gemma


app = create_app()
app.register_blueprint(gemma, url_prefix="/gemma")
app.run(host="0.0.0.0")
