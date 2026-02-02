"""
Background task scheduler for periodic job offer generation.

Provides periodic tasks for automatically generating optimal job offers
for all users with CVs, ensuring fresh recommendations are always available.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from server.database import SessionLocal
from server.models import User
from server.methods.chat import get_optimal_offers_with_cache, identify_ft_parameters
from server.utils.task_cleanup import recover_stale_evaluations

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


async def generate_optimal_offers_for_user(user_id: int, db: Session, force_refresh: bool = False) -> None:
    """
    Generate optimal job offers for a single user.

    Args:
        user_id: ID of the user to generate offers for
        db: Database session
        force_refresh: If True, skip cache and regenerate offers
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            logger.warning(f"User {user_id} not found, skipping optimal offers generation")
            return

        if not user.cv_text or not user.cv_text.strip():
            logger.debug(f"User {user_id} has no CV, skipping optimal offers generation")
            return

        logger.info(f"Generating optimal offers for user {user_id} ({user.username})")

        # Identify France Travail parameters from CV
        ft_result = await identify_ft_parameters(
            user.cv_text,
            preferences=None,
            matching_context=user.matching_context
        )
        ft_parameters = ft_result.get("parameters", {})

        # Generate optimal offers (will be cached in database)
        # Always force refresh for scheduler - no caching
        await get_optimal_offers_with_cache(
            current_user=user,
            db=db,
            ft_parameters=ft_parameters,
            preferences=None,
            top_k=5,
            cache_hours=1,  # 1 hour cache for frontend reads only
            force_refresh=True  # Always regenerate for scheduler tasks
        )

        logger.info(f"Successfully generated optimal offers for user {user_id}")

    except Exception as e:
        logger.error(f"Error generating optimal offers for user {user_id}: {str(e)}")
        db.rollback()  # Rollback to keep session active for next user
        # Don't raise - continue processing other users


async def generate_optimal_offers_for_all_users() -> None:
    """
    Periodic task to generate optimal job offers for all users with CVs.

    This task runs hourly to ensure users always have fresh job recommendations.
    Only processes users who have uploaded a CV.
    """
    logger.info("Starting periodic optimal offers generation for all users")

    db = SessionLocal()
    try:
        # Get all users who have a CV
        users_with_cv = db.query(User).filter(
            User.cv_text.isnot(None),
            User.cv_text != ""
        ).all()

        logger.info(f"Found {len(users_with_cv)} users with CVs")

        for user in users_with_cv:
            await generate_optimal_offers_for_user(user.id, db)

        logger.info("Completed periodic optimal offers generation for all users")

    except Exception as e:
        logger.error(f"Error in periodic optimal offers generation: {str(e)}")
    finally:
        db.close()


async def recover_stale_evaluations_task() -> None:
    """
    Periodic task to recover stale CV evaluations.

    Marks any pending evaluations that have been in progress for too long as failed.
    This prevents the frontend from getting stuck waiting for evaluations that hung or crashed.
    """
    db = SessionLocal()
    try:
        logger.info("Starting stale evaluation recovery")

        # Check for evaluations stuck in pending state for more than 30 minutes
        recovered_count = recover_stale_evaluations(db, stale_after_minutes=30)

        if recovered_count > 0:
            logger.info(f"Recovered {recovered_count} stale evaluations")

    except Exception as e:
        logger.error(f"Error in stale evaluation recovery task: {e}", exc_info=True)
    finally:
        db.close()


def start_scheduler() -> None:
    """
    Initialize and start the background task scheduler.

    Sets up periodic tasks for generating optimal job offers.
    Should be called during application startup.
    """
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already running, skipping initialization")
        return

    logger.info("Initializing background task scheduler")

    scheduler = AsyncIOScheduler()

    # Schedule optimal offers generation to run every hour
    scheduler.add_job(
        generate_optimal_offers_for_all_users,
        trigger=IntervalTrigger(hours=1),
        id="generate_optimal_offers",
        name="Generate optimal offers for all users",
        replace_existing=True,
        next_run_time=datetime.now()  # Run immediately on startup
    )

    # Schedule stale evaluation recovery to run every 5 minutes
    scheduler.add_job(
        recover_stale_evaluations_task,
        trigger=IntervalTrigger(minutes=5),
        id="recover_stale_evaluations",
        name="Recover stale CV evaluations",
        replace_existing=True,
        next_run_time=datetime.now() + timedelta(minutes=1)  # Start after 1 minute
    )

    scheduler.start()
    logger.info("Background task scheduler started successfully")


def shutdown_scheduler() -> None:
    """
    Shutdown the background task scheduler.

    Should be called during application shutdown.
    """
    global scheduler

    if scheduler is None:
        logger.warning("Scheduler not running, nothing to shutdown")
        return

    logger.info("Shutting down background task scheduler")
    scheduler.shutdown(wait=True)
    scheduler = None
    logger.info("Background task scheduler shutdown complete")


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """
    Get the current scheduler instance.

    Returns:
        The scheduler instance if running, None otherwise
    """
    return scheduler

