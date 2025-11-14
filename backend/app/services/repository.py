import os
import shutil
import tempfile
from pathlib import Path
from git import Repo, GitCommandError
from typing import Optional
from app.core.config import settings

class RepositoryService:
    """Service for managing repository operations"""

    @staticmethod
    def clone_repository(clone_url: str, access_token: str) -> Optional[str]:
        """Clone a repository and return the local path"""
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix="gitanalyser_")

            # Add authentication to clone URL
            if "github.com" in clone_url:
                auth_url = clone_url.replace(
                    "https://github.com",
                    f"https://{access_token}@github.com"
                )
            else:
                auth_url = clone_url

            # Clone repository
            Repo.clone_from(
                auth_url,
                temp_dir,
                depth=1,  # Shallow clone for faster performance
                timeout=settings.CLONE_TIMEOUT
            )

            return temp_dir

        except GitCommandError as e:
            print(f"Error cloning repository: {e}")
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return None

    @staticmethod
    def cleanup_repository(repo_path: str):
        """Clean up cloned repository"""
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
        except Exception as e:
            print(f"Error cleaning up repository: {e}")

    @staticmethod
    def get_latest_commit_sha(repo_path: str) -> Optional[str]:
        """Get the latest commit SHA from a cloned repository"""
        try:
            repo = Repo(repo_path)
            return repo.head.commit.hexsha
        except Exception as e:
            print(f"Error getting commit SHA: {e}")
            return None
