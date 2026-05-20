from dotenv import load_dotenv
load_dotenv()

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_file, session
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, CSRFError
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import logging
import os
import sys
import sqlite3

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from business_outreach import fetch_and_save_businesses, generate_outreach_message
from database.manage_templates import add_template, get_all_templates, delete_template, update_template
from outreach.email_sender import send_email, get_email_template, build_recipient_email
from reports.report_generator import generate_report
from integrations.n8n_connector import send_to_n8n

# ---------------------------------------------------------------------------
# Logging  [FIX #8]
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log"),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-production")

# Session timeout — 8 hours  [FIX #6]
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
# Set to True when running behind HTTPS (nginx/load balancer)
app.config["SESSION_COOKIE_SECURE"] = os.getenv("HTTPS", "false").lower() == "true"

# CSRF protection  [FIX #5]
app.config["WTF_CSRF_TIME_LIMIT"] = 3600  # 1-hour token expiry
csrf = CSRFProtect(app)

# Rate limiting — protect login from brute-force  [FIX #4]
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],          # no blanket limit; applied per-route
    storage_uri="memory://",
)

PER_PAGE = 10  # rows per page

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _get_password_hash():
    stored_hash = os.getenv("ADMIN_PASSWORD_HASH")
    if stored_hash:
        return stored_hash
    plaintext = os.getenv("ADMIN_PASSWORD")
    if plaintext:
        return generate_password_hash(plaintext)
    logger.warning(
        "No ADMIN_PASSWORD set — using insecure default. "
        "Set ADMIN_USERNAME and ADMIN_PASSWORD in .env before deploying."
    )
    return generate_password_hash("admin123")


_PASSWORD_HASH = None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sanitize_input(value, max_length=500):
    if not value:
        return ""
    return str(value).strip()[:max_length]


def get_db_connection():
    # check_same_thread=False is safe here because each request gets its
    # own connection that is closed before the response is returned  [FIX #9]
    conn = sqlite3.connect("businesses.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------------------------------------------------------------------
# Error handlers  [FIX #7]
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    logger.warning(f"404 — {request.path}")
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 — {request.path}: {e}")
    return render_template("errors/500.html"), 500


@app.errorhandler(CSRFError)
def csrf_error(e):
    logger.warning(f"CSRF error on {request.path}: {e.description}")
    flash("Your session expired or the request was invalid. Please try again.", "error")
    return redirect(url_for("index")), 400

# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")   # [FIX #4] brute-force protection
def login():
    if session.get("logged_in"):
        return redirect(url_for("index"))

    if request.method == "POST":
        global _PASSWORD_HASH
        if _PASSWORD_HASH is None:
            _PASSWORD_HASH = _get_password_hash()

        username = sanitize_input(request.form.get("username", ""))
        password = request.form.get("password", "")
        expected_user = os.getenv("ADMIN_USERNAME", "admin")

        if username == expected_user and check_password_hash(_PASSWORD_HASH, password):
            session.permanent = True   # honour PERMANENT_SESSION_LIFETIME
            session["logged_in"] = True
            session["username"] = username
            logger.info(f"Login success: {username} from {request.remote_addr}")
            flash(f"Welcome back, {username}!", "success")
            return redirect(url_for("index"))
        else:
            logger.warning(f"Login failed for '{username}' from {request.remote_addr}")
            flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    username = session.get("username", "unknown")
    session.clear()
    logger.info(f"Logout: {username}")
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

# ---------------------------------------------------------------------------
# Protected routes
# ---------------------------------------------------------------------------

@app.route("/")
@login_required
def index():
    search = sanitize_input(request.args.get("q", ""), max_length=200)
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1

    conn = get_db_connection()
    if search:
        like = f"%{search}%"
        total = conn.execute(
            "SELECT COUNT(*) FROM businesses WHERE name LIKE ? OR address LIKE ? OR website LIKE ?",
            (like, like, like),
        ).fetchone()[0]
        businesses = conn.execute(
            "SELECT * FROM businesses WHERE name LIKE ? OR address LIKE ? OR website LIKE ?"
            " ORDER BY name LIMIT ? OFFSET ?",
            (like, like, like, PER_PAGE, (page - 1) * PER_PAGE),
        ).fetchall()
    else:
        total = conn.execute("SELECT COUNT(*) FROM businesses").fetchone()[0]
        businesses = conn.execute(
            "SELECT * FROM businesses ORDER BY name LIMIT ? OFFSET ?",
            (PER_PAGE, (page - 1) * PER_PAGE),
        ).fetchall()

    templates = get_all_templates()
    conn.close()

    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = min(page, total_pages)

    return render_template(
        "index.html",
        businesses=businesses,
        templates=templates,
        page=page,
        total_pages=total_pages,
        total=total,
        per_page=PER_PAGE,
        search=search,
    )


@app.route("/fetch", methods=["POST"])
@login_required
def fetch():
    query = sanitize_input(request.form.get("query", ""))
    location = sanitize_input(request.form.get("location", ""))
    if not query or not location:
        flash("Query and location are required.", "error")
        return redirect(url_for("index"))
    result = fetch_and_save_businesses(query, location)
    if result is None:
        flash("Failed to fetch businesses — check the API key or network connection.", "error")
    elif len(result) == 0:
        flash(f"No businesses found for '{query}'. Try a different query.", "error")
    else:
        flash(f"Fetched {len(result)} business(es) for '{query}'.", "success")
    logger.info(f"{session.get('username')} fetched '{query}' — {len(result) if result else 0} results")
    return redirect(url_for("index"))


@app.route("/add_template", methods=["POST"])
@login_required
def add_template_route():
    name = sanitize_input(request.form.get("name", ""))
    subject = sanitize_input(request.form.get("subject", ""))
    body = sanitize_input(request.form.get("body", ""), max_length=5000)
    if not name or not subject or not body:
        flash("Template name, subject, and body are all required.", "error")
        return redirect(url_for("index"))
    add_template(name, subject, body)
    logger.info(f"{session.get('username')} added template '{name}'")
    flash(f"Successfully added template: {name}", "success")
    return redirect(url_for("index"))


@app.route("/edit_template/<int:template_id>", methods=["POST"])
@login_required
def edit_template_route(template_id):
    subject = sanitize_input(request.form.get("subject", ""))
    body = sanitize_input(request.form.get("body", ""), max_length=5000)
    if not subject or not body:
        flash("Subject and body are required.", "error")
        return redirect(url_for("index"))
    update_template(template_id, subject, body)
    logger.info(f"{session.get('username')} updated template {template_id}")
    flash("Template updated successfully.", "success")
    return redirect(url_for("index"))


@app.route("/delete_template/<int:template_id>", methods=["POST"])
@login_required
def delete_template_route(template_id):
    delete_template(template_id)
    logger.info(f"{session.get('username')} deleted template {template_id}")
    flash("Template deleted.", "success")
    return redirect(url_for("index"))


@app.route("/send_outreach", methods=["POST"])
@login_required
def send_outreach_route():
    template_name = sanitize_input(request.form.get("template_name", ""))
    template = get_email_template(template_name) if template_name else None
    if not template:
        flash("Template not found. Please select a valid template.", "error")
        return redirect(url_for("index"))

    conn = get_db_connection()
    businesses = conn.execute("SELECT * FROM businesses").fetchall()
    conn.close()

    if not businesses:
        flash("No businesses in the database to send outreach to.", "error")
        return redirect(url_for("index"))

    sent, skipped = 0, 0
    for business in businesses:
        to_email = build_recipient_email(business["website"])
        if not to_email:
            skipped += 1
            continue
        subject = template["subject"].format(business_name=business["name"])
        body = generate_outreach_message(business["name"], business["website"])
        send_email(to_email, subject, body)
        sent += 1

    msg = f"Outreach sent to {sent} business(es)."
    if skipped:
        msg += f" {skipped} skipped (no valid website/email)."
    logger.info(f"{session.get('username')} sent outreach — {sent} sent, {skipped} skipped")
    flash(msg, "success")
    return redirect(url_for("index"))


@app.route("/generate_report")
@login_required
def generate_report_route():
    conn = get_db_connection()
    businesses = conn.execute("SELECT name, address, website FROM businesses").fetchall()
    conn.close()
    businesses = [(b["name"], b["address"], b["website"]) for b in businesses]
    report_path = generate_report(businesses)
    logger.info(f"{session.get('username')} downloaded report ({len(businesses)} rows)")
    return send_file(report_path, as_attachment=True)


@app.route("/send_to_n8n", methods=["POST"])
@login_required
def send_to_n8n_route():
    webhook_url = sanitize_input(request.form.get("webhook_url", ""), max_length=2000)
    if not webhook_url:
        flash("Please provide an n8n webhook URL.", "error")
        return redirect(url_for("index"))

    conn = get_db_connection()
    businesses = conn.execute("SELECT * FROM businesses").fetchall()
    conn.close()

    data_to_send = [dict(row) for row in businesses]
    ok = send_to_n8n(webhook_url, data_to_send)
    if ok:
        logger.info(f"{session.get('username')} sent {len(data_to_send)} records to n8n")
        flash(f"Successfully sent {len(data_to_send)} business(es) to n8n.", "success")
    else:
        logger.error(f"n8n send failed for {session.get('username')} — url: {webhook_url[:60]}")
        flash("Failed to send data to n8n — check the webhook URL and network.", "error")
    return redirect(url_for("index"))


@app.route("/edit_business/<int:business_id>", methods=["POST"])
@login_required
def edit_business(business_id):
    name = sanitize_input(request.form.get("name", ""))
    address = sanitize_input(request.form.get("address", ""))
    website = sanitize_input(request.form.get("website", ""))
    if not name:
        flash("Business name is required.", "error")
        return redirect(url_for("index"))
    conn = get_db_connection()
    conn.execute(
        "UPDATE businesses SET name=?, address=?, website=? WHERE id=?",
        (name, address, website, business_id),
    )
    conn.commit()
    conn.close()
    logger.info(f"{session.get('username')} edited business {business_id} → '{name}'")
    flash(f"Business '{name}' updated successfully.", "success")
    return redirect(url_for("index"))


@app.route("/delete_business/<int:business_id>", methods=["POST"])
@login_required
def delete_business(business_id):
    conn = get_db_connection()
    business = conn.execute("SELECT name FROM businesses WHERE id=?", (business_id,)).fetchone()
    if business:
        conn.execute("DELETE FROM businesses WHERE id=?", (business_id,))
        conn.commit()
        logger.info(f"{session.get('username')} deleted business '{business['name']}'")
        flash(f"Business '{business['name']}' deleted.", "success")
    conn.close()
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Entry point — dev only  [FIX #1]
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    if debug:
        logger.warning("Running in DEBUG mode — do not use in production!")
    app.run(debug=debug, host="0.0.0.0", port=port)
