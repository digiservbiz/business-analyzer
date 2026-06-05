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


def _imap_check_job() -> None:
    try:
        from integrations.imap_monitor import check_replies
        found = check_replies()
        if found:
            logger.info("IMAP check: %d new replies detected", found)
    except Exception as exc:
        logger.error("IMAP check error: %s", exc)


def _sequences_job() -> None:
    try:
        from database.manage_sequences import get_due_enrollments, get_steps, advance_enrollment
        from outreach.email_sender import send_email

        enrollments = get_due_enrollments()
        sent = 0
        for enr in enrollments:
            steps = get_steps(enr["sequence_id"])
            step_idx = enr["current_step"] - 1
            if step_idx >= len(steps):
                advance_enrollment(enr["id"], 0, 0, completed=True)
                continue

            step = steps[step_idx]
            price_str = (
                f"${enr['asking_price']:,.0f}"
                if enr["asking_price"] and enr["asking_price"] > 0
                else "a competitive price"
            )
            try:
                subject = step["subject_template"].format(
                    domain=enr["domain_name"],
                    contact_name=enr["contact_name"] or "there",
                    business_name=enr["business_name"] or "your business",
                )
                body = step["body_template"].format(
                    domain=enr["domain_name"],
                    contact_name=enr["contact_name"] or "there",
                    business_name=enr["business_name"] or "your business",
                    asking_price=price_str,
                )
            except KeyError:
                subject = step["subject_template"]
                body = step["body_template"]

            to_email = (enr["contact_email"] or "").strip()
            if to_email:
                send_email(to_email, subject, body)
                sent += 1

            # Advance to next step or complete
            next_step = enr["current_step"] + 1
            if next_step > len(steps):
                advance_enrollment(enr["id"], 0, 0, completed=True)
            else:
                next_delay = steps[step_idx + 1]["delay_days"]
                advance_enrollment(enr["id"], next_step, next_delay)

        if sent:
            logger.info("Sequences: %d step emails sent", sent)
    except Exception as exc:
        logger.error("Sequences job error: %s", exc)


def _news_job():
    """Check company news for buying signals every 6 hours."""
    try:
        from integrations.news_monitor import check_news
        count = check_news()
        if count:
            logger.info("News job: %d new alerts", count)
    except Exception as exc:
        logger.error("News job error: %s", exc)


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
    # Check inbox for replies every 2 hours
    _scheduler.add_job(
        _imap_check_job,
        "interval",
        hours=2,
        id="imap_reply_check",
        replace_existing=True,
    )
    # Process sequence steps every hour
    _scheduler.add_job(
        _sequences_job,
        "interval",
        hours=1,
        id="sequence_steps",
        replace_existing=True,
    )
    _scheduler.add_job(
        _news_job,
        "interval",
        hours=6,
        id="news_monitor",
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
