"""
Background job scheduler for automated campaigns and follow-ups.
Uses APScheduler BackgroundScheduler (runs in same process as Gunicorn worker).
"""
import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def _campaigns_job() -> None:
    try:
        from integrations.campaign import run_all_campaigns
        from database.manage_campaigns import log_campaign_run
        results = run_all_campaigns()
        for r in results:
            log_campaign_run(r["domain_id"], r)
        total = sum(r["emails_sent"] for r in results)
        logger.info("Scheduled campaigns: %d domains, %d emails sent", len(results), total)
    except Exception as exc:
        logger.error("Scheduled campaigns error: %s", exc)


def _followups_job() -> None:
    try:
        from integrations.campaign import send_followups
        sent = send_followups()
        logger.info("Scheduled follow-ups: %d emails sent", sent)
    except Exception as exc:
        logger.error("Scheduled follow-ups error: %s", exc)


def start_scheduler() -> None:
    """Start the background scheduler. Safe to call multiple times."""
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    campaign_hour = int(os.getenv("CAMPAIGN_HOUR", "9"))
    followup_hour = int(os.getenv("FOLLOWUP_HOUR", "10"))

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        _campaigns_job,
        CronTrigger(hour=campaign_hour, minute=0),
        id="daily_campaigns",
        replace_existing=True,
    )
    _scheduler.add_job(
        _followups_job,
        CronTrigger(hour=followup_hour, minute=0),
        id="daily_followups",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "Scheduler started — campaigns at %02d:00 UTC, follow-ups at %02d:00 UTC",
        campaign_hour, followup_hour,
    )


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


def get_scheduler_status() -> dict:
    if not _scheduler or not _scheduler.running:
        return {"running": False, "jobs": []}
    jobs = [
        {"id": j.id, "next_run": str(j.next_run_time)}
        for j in _scheduler.get_jobs()
    ]
    return {"running": True, "jobs": jobs}
