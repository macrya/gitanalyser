from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    analysis_id = Column(Integer, ForeignKey("analyses.id"))

    github_pr_number = Column(Integer)
    github_pr_url = Column(String)
    title = Column(String, nullable=False)
    description = Column(Text)
    branch_name = Column(String, nullable=False)

    status = Column(String, default="draft")  # draft, open, merged, closed
    files_changed = Column(Integer, default=0)
    suggestions_applied = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    merged_at = Column(DateTime)
    closed_at = Column(DateTime)

    # Relationships
    repository = relationship("Repository", back_populates="pull_requests")
    analysis = relationship("Analysis")
