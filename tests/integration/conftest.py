import pytest

from gn3.app import create_app

@pytest.fixture(scope="session")
def client():
    # Do some setup
    app = create_app()
    app.config.update({"TESTING": True})
    app.testing = True
    yield app.test_client()
    # Do some teardown/cleanup
