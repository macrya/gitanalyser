"""
GitHub Webhooks API for automatic repository sync
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
import hmac
import hashlib
import logging
from app.core.database import get_db
from app.core.config import settings
from app.models.repository import Repository as RepositoryModel
from app.models.user import User as UserModel

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify GitHub webhook signature

    Args:
        payload: Raw request body
        signature: X-Hub-Signature-256 header value
        secret: Webhook secret

    Returns:
        True if signature is valid
    """
    if not signature:
        return False

    # GitHub sends sha256=<hash>
    hash_algorithm, github_signature = signature.split('=', 1)

    if hash_algorithm != 'sha256':
        return False

    # Calculate expected signature
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    expected_signature = mac.hexdigest()

    # Constant-time comparison
    return hmac.compare_digest(expected_signature, github_signature)


@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
    x_github_event: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Handle GitHub webhook events

    Supported events:
    - push: Trigger analysis on push
    - repository: Handle repository changes
    - ping: Webhook verification
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify webhook signature (if secret is configured)
    webhook_secret = getattr(settings, 'GITHUB_WEBHOOK_SECRET', None)
    if webhook_secret and x_hub_signature_256:
        if not verify_webhook_signature(body, x_hub_signature_256, webhook_secret):
            logger.warning("Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )

    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )

    # Handle different event types
    event_type = x_github_event

    if event_type == "ping":
        return handle_ping(payload)
    elif event_type == "push":
        return await handle_push(payload, db)
    elif event_type == "repository":
        return await handle_repository(payload, db)
    else:
        logger.info(f"Unhandled webhook event: {event_type}")
        return {"message": f"Event {event_type} received but not handled"}


def handle_ping(payload: dict):
    """Handle ping event (webhook verification)"""
    logger.info("Received ping webhook")
    return {
        "message": "pong",
        "hook_id": payload.get("hook_id"),
        "zen": payload.get("zen")
    }


async def handle_push(payload: dict, db: Session):
    """
    Handle push event - trigger analysis if configured

    Args:
        payload: Webhook payload
        db: Database session

    Returns:
        Response dict
    """
    try:
        repo_data = payload.get("repository", {})
        repo_id = repo_data.get("id")
        ref = payload.get("ref", "")
        commits = payload.get("commits", [])

        logger.info(f"Push to {repo_data.get('full_name')} ({ref}), {len(commits)} commits")

        # Find repository in database
        repository = db.query(RepositoryModel).filter(
            RepositoryModel.github_id == repo_id
        ).first()

        if not repository:
            logger.warning(f"Repository {repo_id} not found in database")
            return {"message": "Repository not tracked"}

        # Only analyze pushes to default branch
        default_branch = f"refs/heads/{repository.default_branch}"
        if ref != default_branch:
            return {"message": f"Skipping non-default branch: {ref}"}

        # TODO: Trigger background analysis here
        # For now, just log the event
        logger.info(f"Would trigger analysis for repository {repository.id}")

        return {
            "message": "Push event processed",
            "repository": repository.full_name,
            "commits": len(commits)
        }

    except Exception as e:
        logger.error(f"Failed to handle push event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def handle_repository(payload: dict, db: Session):
    """
    Handle repository events (created, deleted, renamed, etc.)

    Args:
        payload: Webhook payload
        db: Database session

    Returns:
        Response dict
    """
    try:
        action = payload.get("action")
        repo_data = payload.get("repository", {})
        repo_id = repo_data.get("id")

        logger.info(f"Repository {action}: {repo_data.get('full_name')}")

        repository = db.query(RepositoryModel).filter(
            RepositoryModel.github_id == repo_id
        ).first()

        if action == "deleted" and repository:
            # Remove repository from database
            db.delete(repository)
            db.commit()
            logger.info(f"Deleted repository {repository.full_name}")
            return {"message": "Repository deleted"}

        elif action == "renamed" and repository:
            # Update repository name
            repository.name = repo_data.get("name")
            repository.full_name = repo_data.get("full_name")
            db.commit()
            logger.info(f"Renamed repository to {repository.full_name}")
            return {"message": "Repository renamed"}

        elif action == "archived" and repository:
            # Mark as inactive or delete
            logger.info(f"Repository {repository.full_name} was archived")
            return {"message": "Repository archived"}

        return {"message": f"Repository {action} event processed"}

    except Exception as e:
        logger.error(f"Failed to handle repository event: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/status")
async def webhook_status():
    """Get webhook configuration status"""
    webhook_secret_configured = bool(getattr(settings, 'GITHUB_WEBHOOK_SECRET', None))

    return {
        "webhook_enabled": True,
        "signature_verification": webhook_secret_configured,
        "supported_events": ["ping", "push", "repository"],
        "endpoint": "/api/webhooks/github"
    }
