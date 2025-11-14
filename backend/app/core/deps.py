from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Validate JWT token and return current user.
    Raises 401 if token is invalid or user not found.
    """
    token = credentials.credentials

    # Verify token and extract payload
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID from token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user (additional validation layer)"""
    return current_user

class RateLimiter:
    """Simple in-memory rate limiter"""
    def __init__(self):
        self.requests = {}

    def check_rate_limit(self, user_id: int, limit: int = 100, window: int = 3600):
        """
        Check if user has exceeded rate limit.
        Args:
            user_id: User ID
            limit: Max requests per window
            window: Time window in seconds
        """
        import time
        current_time = time.time()

        if user_id not in self.requests:
            self.requests[user_id] = []

        # Remove old requests outside window
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if current_time - req_time < window
        ]

        # Check limit
        if len(self.requests[user_id]) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {limit} requests per hour."
            )

        # Add current request
        self.requests[user_id].append(current_time)

rate_limiter = RateLimiter()

def check_rate_limit(current_user: User = Depends(get_current_user)):
    """Dependency for rate limiting"""
    rate_limiter.check_rate_limit(current_user.id)
    return current_user
