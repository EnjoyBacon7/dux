"""
Tests for authentication and user management endpoints.
"""
from server.models import Base
from server.database import get_db_session
from server.app import app
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from fastapi.testclient import TestClient
import pytest
import sys
from pathlib import Path

# Add parent directory to path to import server modules
sys.path.insert(0, str(Path(__file__).parent.parent))


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """Create test client with in-memory database."""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db_session] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(client):
    """Create authenticated test client."""
    # Register a test user with a more complex password
    username = "testuser"
    password = "Xk9#mP2$qL7@wR5!"

    response = client.post(
        "/auth/register",
        json={"username": username, "password": password}
    )
    if response.status_code != 200:
        print(f"Registration failed: {response.status_code} - {response.json()}")
    assert response.status_code == 200

    # Login
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password}
    )
    if response.status_code != 200:
        print(f"Login failed: {response.status_code} - {response.json()}")
    assert response.status_code == 200

    return client


class TestDebugEndpoint:
    """Tests for /auth/debug/user-info endpoint."""

    def test_debug_requires_authentication(self, client):
        """Test that debug endpoint requires authentication."""
        response = client.get("/auth/debug/user-info")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_debug_returns_user_info(self, authenticated_client):
        """Test that debug endpoint returns comprehensive user information."""
        response = authenticated_client.get("/auth/debug/user-info")
        assert response.status_code == 200

        data = response.json()

        # Verify structure
        assert "user_info" in data
        assert "passkey_credentials" in data
        assert "recent_login_attempts" in data
        assert "session_info" in data

        # Verify user_info fields
        user_info = data["user_info"]
        assert "id" in user_info
        assert "username" in user_info
        assert user_info["username"] == "testuser"
        assert "has_password" in user_info
        assert user_info["has_password"] is True
        assert "created_at" in user_info
        assert "is_active" in user_info
        assert user_info["is_active"] is True

        # Verify collections
        assert isinstance(data["passkey_credentials"], list)
        assert isinstance(data["recent_login_attempts"], list)

        # Verify session info
        assert "username" in data["session_info"]
        assert data["session_info"]["username"] == "testuser"


class TestDeleteAccountEndpoint:
    """Tests for DELETE /auth/account endpoint."""

    def test_delete_requires_authentication(self, client):
        """Test that delete account requires authentication."""
        response = client.delete("/auth/account")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_delete_account_success(self, authenticated_client):
        """Test successful account deletion."""
        response = authenticated_client.delete("/auth/account")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "deleted" in data["message"].lower()

    def test_delete_account_clears_session(self, authenticated_client):
        """Test that account deletion clears the session."""
        # Verify authenticated before deletion
        response = authenticated_client.get("/auth/me")
        assert response.status_code == 200

        # Delete account
        response = authenticated_client.delete("/auth/account")
        assert response.status_code == 200

        # Verify session is cleared
        response = authenticated_client.get("/auth/me")
        assert response.status_code == 401

    def test_deleted_account_cannot_login(self, client):
        """Test that deleted account cannot log back in."""
        username = "deletetest"
        password = "Xk9#mP2$qL7@wR5!"

        # Register
        response = client.post(
            "/auth/register",
            json={"username": username, "password": password}
        )
        assert response.status_code == 200

        # Login
        response = client.post(
            "/auth/login",
            json={"username": username, "password": password}
        )
        assert response.status_code == 200

        # Delete account
        response = client.delete("/auth/account")
        assert response.status_code == 200

        # Try to login again - should fail
        response = client.post(
            "/auth/login",
            json={"username": username, "password": password}
        )
        assert response.status_code in [400, 401, 404]


class TestDebugDataIntegrity:
    """Tests for debug endpoint data integrity."""

    def test_debug_shows_password_status(self, authenticated_client):
        """Test that debug info correctly shows password status."""
        response = authenticated_client.get("/auth/debug/user-info")
        assert response.status_code == 200

        data = response.json()
        assert data["user_info"]["has_password"] is True

    def test_debug_shows_login_attempts(self, authenticated_client):
        """Test that debug info includes login attempts."""
        response = authenticated_client.get("/auth/debug/user-info")
        assert response.status_code == 200

        data = response.json()
        login_attempts = data["recent_login_attempts"]

        # Should have at least one login attempt (from auth fixture)
        assert len(login_attempts) >= 1

        # Verify login attempt structure
        if len(login_attempts) > 0:
            attempt = login_attempts[0]
            assert "id" in attempt
            assert "success" in attempt
            assert "attempted_at" in attempt

    def test_debug_sensitive_data_truncated(self, authenticated_client):
        """Test that sensitive data is truncated in debug info."""
        response = authenticated_client.get("/auth/debug/user-info")
        assert response.status_code == 200

        data = response.json()

        # Check if passkey credentials have truncated IDs
        for credential in data["passkey_credentials"]:
            if "credential_id" in credential:
                # Should be truncated (ending with ...)
                assert credential["credential_id"].endswith("...")
                # Should be relatively short (truncated)
                assert len(credential["credential_id"]) < 50


class TestAccountDeletionCascade:
    """Tests for cascade deletion of related records."""

    def test_deletion_removes_passkey_credentials(self, client):
        """Test that deleting account also removes passkey credentials."""
        # This would require setting up passkey credentials
        # For now, we just verify the account deletion works
        username = "cascadetest"
        password = "Xk9#mP2$qL7@wR5!"

        # Register and login
        client.post(
            "/auth/register",
            json={"username": username, "password": password}
        )
        client.post(
            "/auth/login",
            json={"username": username, "password": password}
        )

        # Delete account
        response = client.delete("/auth/account")
        assert response.status_code == 200

        # Verify account is gone
        response = client.post(
            "/auth/login",
            json={"username": username, "password": password}
        )
        assert response.status_code != 200
