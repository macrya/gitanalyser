"""
Tests for authentication API
"""
import pytest
from unittest.mock import patch, MagicMock


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_github_login_url(client):
    """Test GitHub OAuth URL generation"""
    response = client.get("/api/auth/github")
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert "github.com/login/oauth/authorize" in data["url"]


@patch('app.api.auth.GitHubService.exchange_code_for_token')
@patch('app.api.auth.GitHubService.get_user_info')
def test_github_callback_new_user(mock_user_info, mock_exchange, client, db_session):
    """Test GitHub OAuth callback for new user"""
    # Mock GitHub responses
    mock_exchange.return_value = "github_access_token"
    mock_user_info.return_value = {
        "id": 99999,
        "login": "newuser",
        "email": "newuser@example.com",
        "avatar_url": "https://avatar.url"
    }

    response = client.post(
        "/api/auth/github/callback",
        json={"code": "test_code"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Verify user was created
    from app.models.user import User
    user = db_session.query(User).filter(User.github_id == 99999).first()
    assert user is not None
    assert user.username == "newuser"


@patch('app.api.auth.GitHubService.exchange_code_for_token')
@patch('app.api.auth.GitHubService.get_user_info')
def test_github_callback_existing_user(mock_user_info, mock_exchange, client, test_user):
    """Test GitHub OAuth callback for existing user"""
    mock_exchange.return_value = "new_github_token"
    mock_user_info.return_value = {
        "id": test_user.github_id,
        "login": test_user.username,
        "email": "updated@example.com",
        "avatar_url": "https://new-avatar.url"
    }

    response = client.post(
        "/api/auth/github/callback",
        json={"code": "test_code"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_github_callback_invalid_code(client):
    """Test GitHub OAuth callback with invalid code"""
    with patch('app.api.auth.GitHubService.exchange_code_for_token', return_value=None):
        response = client.post(
            "/api/auth/github/callback",
            json={"code": "invalid_code"}
        )
        assert response.status_code == 400
