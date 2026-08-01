# config.py
import os
from dotenv import load_dotenv, find_dotenv

# Determine the project root (parent of this file) and load .env from there so
# environment variables are consistently loaded regardless of the current CWD.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

# Prefer explicit .env in project root, then any env files discovered by find_dotenv.
env_path = os.path.join(PROJECT_ROOT, ".env")
if not os.path.exists(env_path):
    # fall back to find_dotenv which looks up the tree
    env_path = find_dotenv()

# load_dotenv is called with the explicit path if found; allow it to silently skip if none
if env_path:
    load_dotenv(env_path)
else:
    # No .env found; continue using existing environment (useful in production)
    pass


class Config:
    # WARNING: SECRET_KEY MUST be set via environment variable in production.
    # The hardcoded fallback below is only for local development convenience.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "recruitai")

    # MySQL connection via PyMySQL. If you don't have MySQL running yet,
    # set USE_SQLITE_FALLBACK=1 in your environment to try the app instantly
    # on a local SQLite file instead (same code, same models, zero setup).
    USE_SQLITE_FALLBACK = os.environ.get("USE_SQLITE_FALLBACK", "0") == "1"

    if USE_SQLITE_FALLBACK:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'recruitai.db')}"
    else:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "1") != "0"
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB upload cap

    # SMTP / Email settings (read from environment for security)
    SMTP_HOST = os.environ.get("SMTP_HOST")
    SMTP_PORT = os.environ.get("SMTP_PORT", "587")
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
    SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USERNAME)
    SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "1") == "1"
    SMTP_USE_SSL = os.environ.get("SMTP_USE_SSL", "0") == "1"
