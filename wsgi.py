# import main

print("STARTING WSGI APP")

from gn3.app import create_app

app = create_app()

if __name__ == "__main__":
    print("Starting wsgi app...")
    app.run()
