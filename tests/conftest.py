"""Shared pytest fixtures for Gidamart.

The app is created at import time in src/main.py, so the test environment
variables must be set *before* that module is imported.
"""
import os
import sys

# Use a throwaway in-memory database and dummy secrets for tests.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["FLASK_ENV"] = "testing"
for key in (
    "RECAPTCHA_SITE_KEY",
    "RECAPTCHA_SECRET_KEY",
    "RECAPTCHA_V3_SITE_KEY",
    "RECAPTCHA_V3_SECRET_KEY",
    "MAIL_USERNAME",
    "MAIL_PASSWORD",
):
    os.environ.pop(key, None)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest  # noqa: E402

from src.main import app as flask_app  # noqa: E402
from src.models import db  # noqa: E402


@pytest.fixture()
def app():
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
