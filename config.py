import os
from dotenv import load_dotenv

load_dotenv()


def _env_bool(name, default="False"):
    return os.getenv(name, default).lower() in ("true", "1", "t", "y", "yes")


class Config:
    """Application configuration loaded from environment variables."""

    APP_ENV = os.getenv("APP_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")

    FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
    FLASK_DEBUG = _env_bool("FLASK_DEBUG", "False")

    AUTH_ENABLED = _env_bool("AUTH_ENABLED", "True")
    AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
    AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "")

    AUTH_ADMIN_USERNAME = os.getenv("AUTH_ADMIN_USERNAME") or AUTH_USERNAME
    AUTH_ADMIN_PASSWORD = os.getenv("AUTH_ADMIN_PASSWORD") or AUTH_PASSWORD
    AUTH_USER_USERNAME = os.getenv("AUTH_USER_USERNAME") or os.getenv("AUTH_VIEWER_USERNAME", "")
    AUTH_USER_PASSWORD = os.getenv("AUTH_USER_PASSWORD") or os.getenv("AUTH_VIEWER_PASSWORD", "")

    RATE_LIMIT_ENABLED = _env_bool("RATE_LIMIT_ENABLED", "True")
    RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "120 per minute")

    SESSION_LIFETIME_MINUTES = int(os.getenv("SESSION_LIFETIME_MINUTES", "30"))

    ROLES = ("admin", "user")

    @classmethod
    def is_auth_required(cls):
        """Auth is required when enabled and at least one password is configured."""
        if not cls.AUTH_ENABLED:
            return False
        return bool(cls.AUTH_ADMIN_PASSWORD or cls.AUTH_USER_PASSWORD)

    @classmethod
    def user_credentials(cls):
        """Return mapping of username -> (password, role)."""
        users = {}
        if cls.AUTH_ADMIN_PASSWORD:
            users[cls.AUTH_ADMIN_USERNAME] = (cls.AUTH_ADMIN_PASSWORD, "admin")
        if cls.AUTH_USER_USERNAME and cls.AUTH_USER_PASSWORD:
            users[cls.AUTH_USER_USERNAME] = (cls.AUTH_USER_PASSWORD, "user")
        return users
