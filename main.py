"""Main entry point for project"""

from flask import Flask
app = Flask(__name__)


@app.route("/")
def hello():
    """Test hello world"""
    return "Hello World!"


if __name__ == '__main__':
    app.run()
