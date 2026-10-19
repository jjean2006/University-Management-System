"""Application Configuration Module

Provides database connection parameters and environment fallbacks.
"""

import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_env_file(path=os.path.join(PROJECT_ROOT, ".env")):
    """Loads KEY=VALUE lines from the project's .env file into os.environ.

    Each team member keeps their own MySQL credentials in .env (git-ignored);
    variables already set in the shell take precedence over the file.
    """
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()


class Config:
    """Base application and database configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "ums-institutional-secret-key-2026")

    # Primary Database Connection Parameters
    DB_USER = os.environ.get("DB_USER", "jacob")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
    DB_NAME = os.environ.get("DB_NAME", "university_db")
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.environ.get("DB_PORT", 3307))
    DB_SOCKET = os.environ.get("DB_SOCKET", "/tmp/mysql.sock")

    # Fallback lists for robust connection across container and host environments
    FALLBACK_PORTS = [3307, 3306]
    FALLBACK_SOCKETS = ["/tmp/mysql.sock", "/var/run/mysqld/mysqld.sock"]


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    DEBUG = True
    TESTING = True


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
