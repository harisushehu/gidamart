"""Smoke tests for the Gidamart Flask application."""
import pytest

from src.models import db, User


def test_app_is_created(app):
    assert app is not None
    assert app.config["TESTING"] is True


def test_health_endpoint_reports_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


@pytest.mark.parametrize(
    "path",
    ["/", "/properties", "/services", "/contact", "/login", "/register"],
)
def test_public_pages_load(client, path):
    response = client.get(path)
    assert response.status_code == 200


def test_unknown_page_returns_404(client):
    response = client.get("/this-page-does-not-exist")
    assert response.status_code == 404


def test_profile_requires_login(client):
    response = client.get("/profile")
    # Anonymous users are redirected to the login page.
    assert response.status_code in (301, 302)
    assert "/login" in response.headers["Location"]


def test_user_password_is_hashed_and_checked(app):
    user = User(email="tester@example.com")
    user.set_password("s3cret-pass")
    db.session.add(user)
    db.session.commit()

    saved = User.query.filter_by(email="tester@example.com").first()
    assert saved is not None
    assert saved.password_hash != "s3cret-pass"
    assert saved.check_password("s3cret-pass")
    assert not saved.check_password("wrong-pass")


def test_regular_user_is_not_master_admin(app):
    user = User(email="plain@example.com", is_admin=False, is_master_admin=False)
    user.set_password("x")
    assert not user.is_master()
