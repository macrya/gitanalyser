from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PullRequestBase(BaseModel):
    title: str
    description: Optional[str] = None
    branch_name: str

class PullRequestCreate(PullRequestBase):
    repository_id: int
    analysis_id: Optional[int] = None

class PullRequest(PullRequestBase):
    id: int
    repository_id: int
    analysis_id: Optional[int] = None
    github_pr_number: Optional[int] = None
    github_pr_url: Optional[str] = None
    status: str
    files_changed: int
    suggestions_applied: int
    created_at: datetime
    merged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
