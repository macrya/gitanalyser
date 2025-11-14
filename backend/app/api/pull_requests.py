from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from app.core.database import get_db
from app.schemas.pull_request import PullRequest, PullRequestCreate
from app.models.pull_request import PullRequest as PRModel
from app.models.repository import Repository as RepositoryModel
from app.models.analysis import Analysis as AnalysisModel, CodeSuggestion as SuggestionModel
from app.models.user import User as UserModel
from app.services.github import GitHubService
import random
import string

router = APIRouter()

def get_current_user(db: Session = Depends(get_db)) -> UserModel:
    """Get current user (simplified)"""
    user = db.query(UserModel).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@router.post("/", response_model=PullRequest)
async def create_pull_request(
    analysis_id: int,
    title: str = None,
    description: str = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Create a pull request with automated refactoring"""
    # Get analysis
    analysis = db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    # Get repository
    repository = db.query(RepositoryModel).filter(
        RepositoryModel.id == analysis.repository_id,
        RepositoryModel.user_id == current_user.id
    ).first()

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get high-priority suggestions
    suggestions = (
        db.query(SuggestionModel)
        .filter(
            SuggestionModel.analysis_id == analysis_id,
            SuggestionModel.applied == False
        )
        .order_by(SuggestionModel.priority.desc())
        .limit(10)  # Apply top 10 suggestions
        .all()
    )

    if not suggestions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No suggestions available to apply"
        )

    # Generate branch name
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    branch_name = f"refactor/technical-debt-{random_suffix}"

    try:
        # Create branch
        GitHubService.create_branch(
            current_user.access_token,
            repository.full_name,
            branch_name,
            repository.default_branch
        )

        # Apply suggestions
        files_changed = set()
        for suggestion in suggestions:
            if suggestion.suggested_code and suggestion.original_code:
                try:
                    # Read current file content
                    gh_repo = GitHubService.get_repository(
                        current_user.access_token,
                        repository.full_name
                    )
                    file_content = gh_repo.get_contents(
                        suggestion.file_path,
                        ref=branch_name
                    )

                    # Replace code
                    new_content = file_content.decoded_content.decode('utf-8').replace(
                        suggestion.original_code,
                        suggestion.suggested_code
                    )

                    # Update file
                    GitHubService.update_file(
                        current_user.access_token,
                        repository.full_name,
                        suggestion.file_path,
                        new_content,
                        f"Refactor: {suggestion.title}",
                        branch_name
                    )

                    files_changed.add(suggestion.file_path)
                    suggestion.applied = True

                except Exception as e:
                    print(f"Failed to apply suggestion {suggestion.id}: {e}")

        db.commit()

        # Create PR
        pr_title = title or f"Technical Debt Refactoring - {len(suggestions)} improvements"
        pr_body = description or self._generate_pr_description(analysis, suggestions, files_changed)

        gh_pr = GitHubService.create_pull_request(
            current_user.access_token,
            repository.full_name,
            pr_title,
            pr_body,
            branch_name,
            repository.default_branch
        )

        # Create PR record
        pr = PRModel(
            repository_id=repository.id,
            analysis_id=analysis_id,
            github_pr_number=gh_pr.number,
            github_pr_url=gh_pr.html_url,
            title=pr_title,
            description=pr_body,
            branch_name=branch_name,
            status="open",
            files_changed=len(files_changed),
            suggestions_applied=len(suggestions)
        )

        db.add(pr)
        db.commit()
        db.refresh(pr)

        return pr

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pull request: {str(e)}"
        )

def _generate_pr_description(analysis, suggestions, files_changed) -> str:
    """Generate PR description"""
    desc = f"""## Technical Debt Refactoring

This PR addresses technical debt identified in the automated code analysis.

### Analysis Summary
- **Total Lines Analyzed**: {analysis.total_lines:,}
- **Total Files**: {analysis.total_files}
- **Average Complexity**: {analysis.average_complexity:.2f}
- **Technical Debt Ratio**: {analysis.technical_debt_ratio:.2f}

### Changes Applied
This PR applies {len(suggestions)} code improvements:

"""

    # Group suggestions by type
    by_type = {}
    for s in suggestions:
        if s.suggestion_type not in by_type:
            by_type[s.suggestion_type] = []
        by_type[s.suggestion_type].append(s)

    for suggestion_type, items in by_type.items():
        desc += f"\n#### {suggestion_type.replace('_', ' ').title()}\n"
        for item in items[:5]:  # Limit to 5 per type
            desc += f"- {item.title} in `{item.file_path}`\n"

    desc += f"\n### Files Changed\n"
    for file_path in sorted(files_changed):
        desc += f"- `{file_path}`\n"

    desc += """
### Review Notes
- All changes are based on automated analysis
- Please review each change carefully before merging
- Run tests to ensure functionality is preserved
"""

    return desc

@router.get("/{pr_id}", response_model=PullRequest)
async def get_pull_request(
    pr_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get pull request details"""
    pr = db.query(PRModel).filter(PRModel.id == pr_id).first()
    if not pr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pull request not found"
        )

    # Check access
    repository = db.query(RepositoryModel).filter(
        RepositoryModel.id == pr.repository_id,
        RepositoryModel.user_id == current_user.id
    ).first()

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return pr

@router.get("/repository/{repository_id}", response_model=List[PullRequest])
async def list_pull_requests(
    repository_id: int,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """List pull requests for a repository"""
    repository = db.query(RepositoryModel).filter(
        RepositoryModel.id == repository_id,
        RepositoryModel.user_id == current_user.id
    ).first()

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )

    prs = (
        db.query(PRModel)
        .filter(PRModel.repository_id == repository_id)
        .order_by(PRModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return prs
