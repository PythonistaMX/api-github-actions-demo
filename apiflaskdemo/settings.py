"""Configuracion de la aplicacion."""
import os


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


PATH = os.path.dirname(os.path.abspath(__file__))
ENV = os.getenv("APP_ENV", "dev").lower()

# Solo habilitar debug/testing por variable explicita.
DEBUG = _as_bool(os.getenv("APP_DEBUG"), default=False)
TESTING = _as_bool(os.getenv("APP_TESTING"), default=False)

# Secretos por entorno via GitHub Actions -> Secrets.
SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev-insecure-secret-change-me")
SECURITY_PASSWORD_SALT = os.getenv("APP_SECURITY_PASSWORD_SALT", "dev-insecure-salt-change-me")


def _default_database_uri() -> str:
    if ENV == "prod":
        return "postgresql://postgres:postgres@localhost:5432/postgres"
    if ENV == "test":
        return "sqlite:///test.sqlite3"
    return "sqlite:///db.sqlite3"


_database_url = os.getenv("DATABASE_URL", "").strip() or _default_database_uri()
# Compatibilidad con URLs antiguas tipo postgres://
if _database_url.startswith("postgres://"):
    _database_url = _database_url.replace("postgres://", "postgresql://", 1)

SQLALCHEMY_DATABASE_URI = _database_url
SQLALCHEMY_TRACK_MODIFICATIONS = False
