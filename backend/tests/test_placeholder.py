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


import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from plugins.filesystem import FilesystemPlugin
from src.services.mcp_client import validate_url_ssrf

@pytest.mark.asyncio
async def test_filesystem_plugin_path_traversal():
    plugin = FilesystemPlugin()
    # Traversing up outside working directory is denied
    with pytest.raises(PermissionError):
        await plugin.read_file("../../secret.txt")
    # Inside working directory is permitted
    res = await plugin.read_file("local_test_file.txt")
    assert res == "mocked content"


def test_mcp_client_ssrf_validation():
    # Public domains pass validation
    validate_url_ssrf("https://github.com/sargaprasadrs/NeuroMeshOSS")
    
    # Intranet IP/localhost attempts are blocked
    with pytest.raises(ValueError):
        validate_url_ssrf("http://127.0.0.1:8080/mcp")
        
    with pytest.raises(ValueError):
        validate_url_ssrf("http://169.254.169.254/latest/meta-data")
        
    with pytest.raises(ValueError):
        validate_url_ssrf("http://localhost/mcp")
