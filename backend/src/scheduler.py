"""Background job scheduler."""

from apscheduler.schedulers.background import BackgroundScheduler

from config import get_settings
from database import SessionLocal
from observability.logging import log_operation, logger
from services.health_service import HealthService

_scheduler: BackgroundScheduler | None = None


def run_health_checks() -> None:
    db = SessionLocal()
    try:
        health = HealthService(db)
        results = health.check_all_sites()
        log_operation("scheduler.health_check", sites_checked=len(results))
    except Exception as e:
        logger.error("scheduler.health_check.failed", error=str(e))
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    settings = get_settings()
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        run_health_checks,
        "interval",
        minutes=settings.health_check_interval_minutes,
        id="health_checks",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("scheduler.started", interval_minutes=settings.health_check_interval_minutes)
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
