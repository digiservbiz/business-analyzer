from flask import Blueprint, render_template, request, redirect, url_for, flash
from functools import wraps
from flask import session

news_bp = Blueprint("news", __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@news_bp.route("/news-alerts")
@login_required
def news_alerts():
    from database.manage_news import get_recent_alerts, get_alert_count
    alerts = get_recent_alerts(limit=100, actioned=None)
    unread = get_alert_count(actioned=0)
    return render_template("news_alerts.html", alerts=alerts, unread=unread)


@news_bp.route("/news-alerts/<int:alert_id>/action", methods=["POST"])
@login_required
def action_alert(alert_id):
    from database.manage_news import mark_actioned
    mark_actioned(alert_id)
    return redirect(url_for("news.news_alerts"))


@news_bp.route("/news-alerts/run", methods=["POST"])
@login_required
def run_news_check():
    from integrations.news_monitor import check_news
    count = check_news()
    flash(f"News check complete — {count} new alert(s) found.", "success" if count else "info")
    return redirect(url_for("news.news_alerts"))
