import pytest


@pytest.fixture
def app():
    from app import app as flask_app
    from config import Config

    Config.AUTH_ENABLED = True
    Config.AUTH_ADMIN_USERNAME = "testadmin"
    Config.AUTH_ADMIN_PASSWORD = "testpass"
    Config.AUTH_USER_USERNAME = "testuser"
    Config.AUTH_USER_PASSWORD = "userpass"
    Config.RATE_LIMIT_ENABLED = False

    flask_app.config.update(
        TESTING=True,
        RATELIMIT_ENABLED=False,
        SECRET_KEY="test-secret-key",
    )
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    with client.session_transaction() as sess:
        sess["authenticated"] = True
        sess["username"] = "testadmin"
        sess["role"] = "admin"
    return client


@pytest.fixture
def user_client(client):
    with client.session_transaction() as sess:
        sess["authenticated"] = True
        sess["username"] = "testuser"
        sess["role"] = "user"
    return client
