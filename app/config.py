"""Application Configuration Module

Provides database connection parameters and environment fallbacks.
"""

import os


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
