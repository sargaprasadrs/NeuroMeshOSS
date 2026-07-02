import pytest
from src.config.settings import settings
from src.core.entities.user import User
from src.services.auth_service import AuthService
from src.main import create_app


def test_settings_import():
    assert settings.ENV in ["dev", "staging", "prod"]


def test_user_entity_validation():
    user = User(
        email="test@neuromesh.org",
        password_hash="hashed_string",
    )
    assert user.email == "test@neuromesh.org"
    assert user.role == "user"


def test_password_hashing():
    password = "supersecretpassword"
    hashed = AuthService.get_password_hash(password)
    assert AuthService.verify_password(password, hashed) is True
    assert AuthService.verify_password("wrongpassword", hashed) is False


def test_app_factory():
    app = create_app()
    assert app.title == "NeuroMeshOSS"
