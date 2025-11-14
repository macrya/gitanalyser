from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.auth import Token, GitHubCallback
from app.services.github import GitHubService
from app.models.user import User as UserModel
from datetime import timedelta
from app.core.config import settings

router = APIRouter()

@router.get("/github")
async def github_login():
    """Redirect to GitHub OAuth"""
    auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={settings.GITHUB_CLIENT_ID}&"
        f"redirect_uri={settings.GITHUB_REDIRECT_URI}&"
        f"scope=repo,user,write:repo_hook"
    )
    return {"url": auth_url}

@router.post("/github/callback", response_model=Token)
async def github_callback(callback: GitHubCallback, db: Session = Depends(get_db)):
    """Handle GitHub OAuth callback"""
    # Exchange code for access token
    access_token = await GitHubService.exchange_code_for_token(callback.code)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to obtain access token"
        )

    # Get user info from GitHub
    user_info = await GitHubService.get_user_info(access_token)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user information"
        )

    # Check if user exists
    user = db.query(UserModel).filter(UserModel.github_id == user_info["id"]).first()

    if user:
        # Update existing user
        user.access_token = access_token
        user.username = user_info["login"]
        user.email = user_info.get("email")
        user.avatar_url = user_info.get("avatar_url")
    else:
        # Create new user
        user = UserModel(
            github_id=user_info["id"],
            username=user_info["login"],
            email=user_info.get("email"),
            avatar_url=user_info.get("avatar_url"),
            access_token=access_token
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    # Create JWT token
    token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=token_expires
    )

    return Token(access_token=jwt_token)

@router.get("/me")
async def get_current_user(db: Session = Depends(get_db), user_id: int = None):
    """Get current user information"""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user
