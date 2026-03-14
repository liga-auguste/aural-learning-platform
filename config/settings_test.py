"""
Test settings — verwendet SQLite statt PostgreSQL,
damit keine CREATEDB-Berechtigung nötig ist.

Verwendung:
    python manage.py test --settings=config.settings_test
"""
from config.settings import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",  # noqa: F405
    }
}

# Schnellere Passwort-Hashfunktion in Tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Kein E-Mail-Versand in Tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Kein R2-Storage in Tests — lokale Dateien
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
