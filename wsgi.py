"""
WSGI application entry-point.
"""
# import main
from gn3.app import create_app

print("STARTING WSGI APP")

app = create_app()

if __name__ == "__main__":
    print("Starting wsgi app...")
    app.run()
