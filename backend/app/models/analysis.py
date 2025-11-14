from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum

class SeverityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DebtType(str, enum.Enum):
    CODE_SMELL = "code_smell"
    DUPLICATION = "duplication"
    COMPLEXITY = "complexity"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    commit_sha = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, in_progress, completed, failed

    # Quality Metrics
    total_lines = Column(Integer, default=0)
    total_files = Column(Integer, default=0)
    average_complexity = Column(Float, default=0.0)
    maintainability_index = Column(Float, default=0.0)
    code_coverage = Column(Float, default=0.0)
    technical_debt_ratio = Column(Float, default=0.0)

    # Debt Counts
    total_debt_items = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)

    # Additional metrics
    metrics = Column(JSON, default={})
    error_message = Column(Text)

    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    repository = relationship("Repository", back_populates="analyses")
    debt_items = relationship("TechnicalDebtItem", back_populates="analysis", cascade="all, delete-orphan")
    suggestions = relationship("CodeSuggestion", back_populates="analysis", cascade="all, delete-orphan")

class TechnicalDebtItem(Base):
    __tablename__ = "technical_debt_items"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)

    file_path = Column(String, nullable=False)
    line_number = Column(Integer)
    debt_type = Column(String, nullable=False)  # Use DebtType enum values
    severity = Column(String, nullable=False)  # Use SeverityLevel enum values
    title = Column(String, nullable=False)
    description = Column(Text)
    code_snippet = Column(Text)

    # Metrics
    complexity_score = Column(Float)
    estimated_effort_hours = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis = relationship("Analysis", back_populates="debt_items")

class CodeSuggestion(Base):
    __tablename__ = "code_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)

    file_path = Column(String, nullable=False)
    line_start = Column(Integer)
    line_end = Column(Integer)
    suggestion_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)

    # Code changes
    original_code = Column(Text)
    suggested_code = Column(Text)

    # Metadata
    priority = Column(Integer, default=0)
    confidence = Column(Float, default=0.0)  # 0-1
    impact = Column(String)  # low, medium, high

    applied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis = relationship("Analysis", back_populates="suggestions")
