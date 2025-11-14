import httpx
from github import Github, Auth
from typing import Optional, Dict, Any
from app.core.config import settings

class GitHubService:
    """Service for interacting with GitHub API"""

    @staticmethod
    async def exchange_code_for_token(code: str) -> Optional[str]:
        """Exchange OAuth code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                json={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                },
                headers={"Accept": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
            return None

    @staticmethod
    async def get_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """Get GitHub user information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )

            if response.status_code == 200:
                return response.json()
            return None

    @staticmethod
    def get_client(access_token: str) -> Github:
        """Get authenticated GitHub client"""
        auth = Auth.Token(access_token)
        return Github(auth=auth)

    @staticmethod
    def get_user_repositories(access_token: str, per_page: int = 100):
        """Get user repositories"""
        g = GitHubService.get_client(access_token)
        user = g.get_user()
        return user.get_repos(sort="updated", per_page=per_page)

    @staticmethod
    def get_repository(access_token: str, full_name: str):
        """Get specific repository"""
        g = GitHubService.get_client(access_token)
        return g.get_repo(full_name)

    @staticmethod
    def create_pull_request(
        access_token: str,
        repo_full_name: str,
        title: str,
        body: str,
        head: str,
        base: str = "main"
    ):
        """Create a pull request"""
        g = GitHubService.get_client(access_token)
        repo = g.get_repo(repo_full_name)
        return repo.create_pull(
            title=title,
            body=body,
            head=head,
            base=base
        )

    @staticmethod
    def create_branch(access_token: str, repo_full_name: str, branch_name: str, from_branch: str = "main"):
        """Create a new branch"""
        g = GitHubService.get_client(access_token)
        repo = g.get_repo(repo_full_name)

        # Get the latest commit SHA from the base branch
        ref = repo.get_git_ref(f"heads/{from_branch}")
        sha = ref.object.sha

        # Create new branch
        repo.create_git_ref(f"refs/heads/{branch_name}", sha)
        return branch_name

    @staticmethod
    def update_file(
        access_token: str,
        repo_full_name: str,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str
    ):
        """Update a file in the repository"""
        g = GitHubService.get_client(access_token)
        repo = g.get_repo(repo_full_name)

        try:
            # Get the file to update
            file = repo.get_contents(file_path, ref=branch)
            repo.update_file(
                file_path,
                commit_message,
                content,
                file.sha,
                branch=branch
            )
        except Exception:
            # File doesn't exist, create it
            repo.create_file(
                file_path,
                commit_message,
                content,
                branch=branch
            )
