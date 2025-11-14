from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from app.core.database import get_db
from app.schemas.analysis import Analysis, AnalysisDetail, AnalysisCreate
from app.models.analysis import Analysis as AnalysisModel
from app.models.analysis import TechnicalDebtItem as DebtModel
from app.models.analysis import CodeSuggestion as SuggestionModel
from app.models.repository import Repository as RepositoryModel
from app.models.user import User as UserModel
from app.services.analyzer import CodeAnalyzer
from app.services.repository import RepositoryService
from app.services.github import GitHubService

router = APIRouter()

def get_current_user(db: Session = Depends(get_db)) -> UserModel:
    """Get current user (simplified)"""
    user = db.query(UserModel).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

def perform_analysis(analysis_id: int, repository_id: int, access_token: str, clone_url: str, db_url: str):
    """Background task to perform repository analysis"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Create new database session for background task
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        analysis = db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()
        if not analysis:
            return

        # Update status
        analysis.status = "in_progress"
        analysis.started_at = datetime.utcnow()
        db.commit()

        # Clone repository
        repo_path = RepositoryService.clone_repository(clone_url, access_token)
        if not repo_path:
            analysis.status = "failed"
            analysis.error_message = "Failed to clone repository"
            analysis.completed_at = datetime.utcnow()
            db.commit()
            return

        # Get commit SHA
        commit_sha = RepositoryService.get_latest_commit_sha(repo_path)
        if commit_sha:
            analysis.commit_sha = commit_sha

        # Analyze repository
        analyzer = CodeAnalyzer(repo_path)
        results = analyzer.analyze_repository()

        # Update analysis with results
        analysis.total_lines = results.get("total_lines", 0)
        analysis.total_files = results.get("total_files", 0)
        analysis.average_complexity = results.get("average_complexity", 0.0)
        analysis.maintainability_index = results.get("maintainability_index", 0.0)
        analysis.technical_debt_ratio = results.get("technical_debt_ratio", 0.0)
        analysis.total_debt_items = results.get("total_debt_items", 0)
        analysis.critical_issues = results.get("critical_issues", 0)
        analysis.high_issues = results.get("high_issues", 0)
        analysis.medium_issues = results.get("medium_issues", 0)
        analysis.low_issues = results.get("low_issues", 0)
        analysis.metrics = results.get("metrics", {})

        # Save debt items
        for debt_item in results.get("debt_items", []):
            db_debt = DebtModel(
                analysis_id=analysis.id,
                **debt_item
            )
            db.add(db_debt)

        # Save suggestions
        for suggestion in results.get("suggestions", []):
            db_suggestion = SuggestionModel(
                analysis_id=analysis.id,
                **suggestion
            )
            db.add(db_suggestion)

        # Update repository last_analyzed_at
        repository = db.query(RepositoryModel).filter(RepositoryModel.id == repository_id).first()
        if repository:
            repository.last_analyzed_at = datetime.utcnow()

        analysis.status = "completed"
        analysis.completed_at = datetime.utcnow()
        db.commit()

        # Cleanup
        RepositoryService.cleanup_repository(repo_path)

    except Exception as e:
        analysis.status = "failed"
        analysis.error_message = str(e)
        analysis.completed_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()

@router.post("/", response_model=Analysis)
async def create_analysis(
    repository_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Create and start a new analysis"""
    # Get repository
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

    # Create analysis record
    analysis = AnalysisModel(
        repository_id=repository_id,
        commit_sha="pending",
        status="pending"
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # Get clone URL
    try:
        gh_repo = GitHubService.get_repository(current_user.access_token, repository.full_name)
        clone_url = gh_repo.clone_url
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get repository info: {str(e)}"
        )

    # Start background analysis
    from app.core.config import settings
    background_tasks.add_task(
        perform_analysis,
        analysis.id,
        repository_id,
        current_user.access_token,
        clone_url,
        settings.DATABASE_URL
    )

    return analysis

@router.get("/{analysis_id}", response_model=AnalysisDetail)
async def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get analysis details"""
    analysis = (
        db.query(AnalysisModel)
        .filter(AnalysisModel.id == analysis_id)
        .first()
    )

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    # Check if user owns the repository
    repository = db.query(RepositoryModel).filter(
        RepositoryModel.id == analysis.repository_id,
        RepositoryModel.user_id == current_user.id
    ).first()

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return analysis

@router.get("/repository/{repository_id}", response_model=List[Analysis])
async def list_analyses(
    repository_id: int,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """List analyses for a repository"""
    # Check repository ownership
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

    analyses = (
        db.query(AnalysisModel)
        .filter(AnalysisModel.repository_id == repository_id)
        .order_by(AnalysisModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return analyses
