"""
Task Cleanup and Recovery Utilities

Handles cleanup of pending background tasks on application shutdown,
and recovery of stale pending evaluations.
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from server.models import CVEvaluation

logger = logging.getLogger(__name__)


def cleanup_pending_tasks(db: Session) -> int:
    """
    Mark all pending CV evaluations as failed on application shutdown.

    This ensures the frontend doesn't get stuck waiting for tasks that will never complete.

    Args:
        db: Database session

    Returns:
        Number of tasks marked as failed
    """
    try:
        # Find all pending evaluations
        pending_evaluations = db.query(CVEvaluation).filter(
            CVEvaluation.evaluation_status == "pending"
        ).all()

        failed_count = 0
        for evaluation in pending_evaluations:
            try:
                evaluation.evaluation_status = "failed"
                evaluation.error_message = "Application shutdown while processing. Please try again."
                db.add(evaluation)
                failed_count += 1
                logger.warning(f"Marked pending evaluation {evaluation.id} as failed due to shutdown")
            except Exception as e:
                logger.error(f"Failed to mark evaluation {evaluation.id} as failed: {e}")

        db.commit()
        return failed_count

    except Exception as e:
        logger.error(f"Error cleaning up pending tasks: {e}")
        return 0


def recover_stale_evaluations(db: Session, stale_after_minutes: int = 30) -> int:
    """
    Recovery task to mark evaluations as failed if they've been pending too long.

    This handles cases where background tasks crash or hang without updating the database.
    Runs periodically to clean up stuck evaluations.

    Args:
        db: Database session
        stale_after_minutes: Minutes after which a pending evaluation is considered stale

    Returns:
        Number of stale evaluations recovered
    """
    try:
        stale_threshold = datetime.utcnow() - timedelta(minutes=stale_after_minutes)

        # Find pending evaluations older than threshold
        stale_evaluations = db.query(CVEvaluation).filter(
            CVEvaluation.evaluation_status == "pending",
            CVEvaluation.created_at < stale_threshold
        ).all()

        recovered_count = 0
        for evaluation in stale_evaluations:
            try:
                evaluation.evaluation_status = "failed"
                evaluation.error_message = f"Evaluation timed out after {stale_after_minutes} minutes. Please try again."
                db.add(evaluation)
                recovered_count += 1
                logger.warning(
                    f"Recovered stale evaluation {evaluation.id} "
                    f"(pending since {evaluation.created_at})"
                )
            except Exception as e:
                logger.error(f"Failed to recover evaluation {evaluation.id}: {e}")

        db.commit()
        return recovered_count

    except Exception as e:
        logger.error(f"Error recovering stale evaluations: {e}")
        return 0
