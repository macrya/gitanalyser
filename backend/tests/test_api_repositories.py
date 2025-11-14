"""
Tests for repositories API
"""
import pytest
from unittest.mock import patch, MagicMock


def test_list_repositories_authenticated(client, auth_headers, test_repository):
    """Test listing repositories with authentication"""
    response = client.get("/api/repositories/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "repositories" in data
    assert "total" in data
    assert data["total"] == 1
    assert len(data["repositories"]) == 1
    assert data["repositories"][0]["name"] == "test-repo"


def test_list_repositories_unauthenticated(client):
    """Test listing repositories without authentication"""
    response = client.get("/api/repositories/")
    assert response.status_code == 403


def test_get_repository(client, auth_headers, test_repository):
    """Test getting specific repository"""
    response = client.get(
        f"/api/repositories/{test_repository.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_repository.id
    assert data["name"] == "test-repo"


def test_get_repository_not_found(client, auth_headers):
    """Test getting non-existent repository"""
    response = client.get("/api/repositories/99999", headers=auth_headers)
    assert response.status_code == 404


def test_delete_repository(client, auth_headers, test_repository):
    """Test deleting repository"""
    response = client.delete(
        f"/api/repositories/{test_repository.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "message" in response.json()

    # Verify deletion
    response = client.get(
        f"/api/repositories/{test_repository.id}",
        headers=auth_headers
    )
    assert response.status_code == 404


@patch('app.api.repositories.GitHubService.get_user_repositories')
def test_sync_repositories(mock_get_repos, client, auth_headers, test_user, db_session):
    """Test syncing repositories from GitHub"""
    # Mock GitHub API response
    mock_repo = MagicMock()
    mock_repo.id = 11111
    mock_repo.name = "new-repo"
    mock_repo.full_name = "testuser/new-repo"
    mock_repo.description = "New test repo"
    mock_repo.html_url = "https://github.com/testuser/new-repo"
    mock_repo.default_branch = "main"
    mock_repo.language = "JavaScript"
    mock_repo.private = False
    mock_repo.stargazers_count = 5
    mock_repo.forks_count = 1

    mock_get_repos.return_value = [mock_repo]

    response = client.post("/api/repositories/sync", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "synced_count" in data
    assert data["synced_count"] == 1

    # Verify repository was created
    from app.models.repository import Repository
    repo = db_session.query(Repository).filter(Repository.github_id == 11111).first()
    assert repo is not None
    assert repo.name == "new-repo"
