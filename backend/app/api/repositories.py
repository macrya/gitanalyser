from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.repository import Repository, RepositoryCreate, RepositoryList
from app.models.repository import Repository as RepositoryModel
from app.models.user import User as UserModel
from app.services.github import GitHubService

router = APIRouter()

def get_current_user(db: Session = Depends(get_db)) -> UserModel:
    """Get current user (simplified - in production use proper JWT validation)"""
    # This is a placeholder - implement proper JWT validation
    user = db.query(UserModel).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@router.get("/", response_model=RepositoryList)
async def list_repositories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """List user's repositories"""
    repositories = (
        db.query(RepositoryModel)
        .filter(RepositoryModel.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    total = db.query(RepositoryModel).filter(RepositoryModel.user_id == current_user.id).count()

    return RepositoryList(repositories=repositories, total=total)

@router.post("/sync")
async def sync_repositories(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Sync repositories from GitHub"""
    try:
        repos = GitHubService.get_user_repositories(current_user.access_token)

        synced_count = 0
        for repo in repos:
            # Check if repository already exists
            existing = db.query(RepositoryModel).filter(
                RepositoryModel.github_id == repo.id
            ).first()

            if existing:
                # Update existing repository
                existing.name = repo.name
                existing.full_name = repo.full_name
                existing.description = repo.description
                existing.url = repo.html_url
                existing.default_branch = repo.default_branch
                existing.language = repo.language
                existing.stars = repo.stargazers_count
                existing.forks = repo.forks_count
                existing.is_private = repo.private
            else:
                # Create new repository
                new_repo = RepositoryModel(
                    user_id=current_user.id,
                    github_id=repo.id,
                    name=repo.name,
                    full_name=repo.full_name,
                    description=repo.description,
                    url=repo.html_url,
                    default_branch=repo.default_branch,
                    language=repo.language,
                    is_private=repo.private,
                    stars=repo.stargazers_count,
                    forks=repo.forks_count
                )
                db.add(new_repo)
                synced_count += 1

        db.commit()

        return {
            "message": f"Successfully synced repositories",
            "synced_count": synced_count
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync repositories: {str(e)}"
        )

@router.get("/{repository_id}", response_model=Repository)
async def get_repository(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get repository details"""
    repository = (
        db.query(RepositoryModel)
        .filter(
            RepositoryModel.id == repository_id,
            RepositoryModel.user_id == current_user.id
        )
        .first()
    )

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )

    return repository

@router.delete("/{repository_id}")
async def delete_repository(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Delete repository"""
    repository = (
        db.query(RepositoryModel)
        .filter(
            RepositoryModel.id == repository_id,
            RepositoryModel.user_id == current_user.id
        )
        .first()
    )

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )

    db.delete(repository)
    db.commit()

    return {"message": "Repository deleted successfully"}
