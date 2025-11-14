from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class TechnicalDebtItem(BaseModel):
    id: int
    file_path: str
    line_number: Optional[int] = None
    debt_type: str
    severity: str
    title: str
    description: Optional[str] = None
    code_snippet: Optional[str] = None
    complexity_score: Optional[float] = None
    estimated_effort_hours: Optional[float] = None

    class Config:
        from_attributes = True

class CodeSuggestion(BaseModel):
    id: int
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    suggestion_type: str
    title: str
    description: Optional[str] = None
    original_code: Optional[str] = None
    suggested_code: Optional[str] = None
    priority: int
    confidence: float
    impact: Optional[str] = None
    applied: bool

    class Config:
        from_attributes = True

class AnalysisBase(BaseModel):
    repository_id: int
    commit_sha: str

class AnalysisCreate(AnalysisBase):
    pass

class Analysis(AnalysisBase):
    id: int
    status: str
    total_lines: int
    total_files: int
    average_complexity: float
    maintainability_index: float
    code_coverage: float
    technical_debt_ratio: float
    total_debt_items: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    metrics: Dict[str, Any]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AnalysisDetail(Analysis):
    debt_items: list[TechnicalDebtItem]
    suggestions: list[CodeSuggestion]

    class Config:
        from_attributes = True
