from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RepositoryBase(BaseModel):
    name: str
    full_name: str
    description: Optional[str] = None
    url: str
    default_branch: str = "main"
    language: Optional[str] = None

class RepositoryCreate(RepositoryBase):
    github_id: int
    is_private: bool = False
    stars: int = 0
    forks: int = 0

class RepositoryUpdate(BaseModel):
    description: Optional[str] = None
    default_branch: Optional[str] = None

class Repository(RepositoryBase):
    id: int
    github_id: int
    user_id: int
    is_private: bool
    stars: int
    forks: int
    last_analyzed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RepositoryList(BaseModel):
    repositories: list[Repository]
    total: int
