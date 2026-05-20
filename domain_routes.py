"""
Domain Sales Mode — Flask routes.
Registered as a Blueprint in app.py.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
import os

from domain_analyzer import analyze_domain, is_weak_website, generate_pitch_email
from database.manage_domains import (
    add_domain, get_all_domains, get_domain,
    update_domain_status, delete_domain,
    record_pitch, get_pitched_business_ids,
)
from outreach.email_sender import send_email, build_recipient_email

domains_bp = Blueprint("domains", __name__)


# Reuse login_required from app — imported when blueprint is registered
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def sanitize_input(value, max_length=500):
    if not value:
        return ""
    return str(value).strip()[:max_length]


# Rough city → coordinates lookup for common locations
CITY_COORDS = {
    "Dubai": "25.2048,55.2708", "London": "51.5074,-0.1278",
    "New York": "40.7128,-74.0060", "Los Angeles": "34.0522,-118.2437",
    "Paris": "48.8566,2.3522", "Tokyo": "35.6762,139.6503",
    "Sydney": "-33.8688,151.2093", "Singapore": "1.3521,103.8198",
    "Toronto": "43.6532,-79.3832", "Berlin": "52.5200,13.4050",
    "Mumbai": "19.0760,72.8777",
    "São Paulo": "-23.5505,-46.6333", "Mexico City": "19.4326,-99.1332",
    "Chicago": "41.8781,-87.6298", "Houston": "29.7604,-95.3698",
    "Miami": "25.7617,-80.1918", "San Francisco": "37.7749,-122.4194",
    "Seattle": "47.6062,-122.3321", "Boston": "42.3601,-71.0589",
    "Manchester": "53.4808,-2.2426", "Birmingham": "52.4862,-1.8904",
    "Amsterdam": "52.3676,4.9041", "Barcelona": "41.3851,2.1734",
    "Madrid": "40.4168,-3.7038", "Rome": "41.9028,12.4964",
    "Istanbul": "41.0082,28.9784", "Nairobi": "-1.2921,36.8219",
    "Lagos": "6.5244,3.3792", "Cairo": "30.0444,31.2357",
    "Johannesburg": "-26.2041,28.0473", "Riyadh": "24.7136,46.6753",
    "Kuala Lumpur": "3.1390,101.6869", "Bangkok": "13.7563,100.5018",
    "Seoul": "37.5665,126.9780", "Beijing": "39.9042,116.4074",
    "Shanghai": "31.2304,121.4737",
}


@domains_bp.route("/domains")
@login_required
def domains_list():
    domains = get_all_domains()
    return render_template("domains.html", domains=domains)


@domains_bp.route("/domains/add", methods=["POST"])
@login_required
def domains_add():
    domain_str = sanitize_input(request.form.get("domain", ""))
    asking_price = request.form.get("asking_price", "0") or "0"
    notes = sanitize_input(request.form.get("notes", ""), max_length=1000)

    if not domain_str:
        flash("Domain name is required.", "error")
        return redirect(url_for("domains.domains_list"))

    try:
        asking_price = float(asking_price)
    except ValueError:
        asking_price = 0.0

    # Auto-analyse to fill in industry/location if not provided
    analysis = analyze_domain(domain_str)
    industry = sanitize_input(request.form.get("industry", "")) or analysis["industry"]
    location = sanitize_input(request.form.get("location", "")) or (analysis["location"] or "")
    keywords = ",".join(analysis["tokens"])

    ok = add_domain(domain_str, keywords, industry, location, asking_price, notes)
    if ok:
        flash(f"Domain '{domain_str}' added to portfolio.", "success")
    else:
        flash(f"Domain '{domain_str}' already exists in your portfolio.", "error")

    return redirect(url_for("domains.domains_list"))


@domains_bp.route("/domains/<int:domain_id>/prospects")
@login_required
def domains_prospects(domain_id):
    domain = get_domain(domain_id)
    if not domain:
        flash("Domain not found.", "error")
        return redirect(url_for("domains.domains_list"))

    analysis = analyze_domain(domain["domain"])
    # Override with stored values if they exist
    if domain["industry"]:
        analysis["industry"] = domain["industry"]
    if domain["location"]:
        analysis["location"] = domain["location"]
        if domain["location"] in CITY_COORDS:
            analysis["search_query"] = f"{analysis['industry']} in {domain['location']}"

    coord_hint = CITY_COORDS.get(analysis.get("location", ""), "")

    return render_template(
        "domain_prospects.html",
        domain=domain,
        analysis=analysis,
        coord_hint=coord_hint,
        prospects=None,
        weak_count=0,
    )


@domains_bp.route("/domains/<int:domain_id>/fetch-prospects", methods=["POST"])
@login_required
def domains_fetch_prospects(domain_id):
    from business_outreach import fetch_and_save_businesses
    import sqlite3

    domain = get_domain(domain_id)
    if not domain:
        flash("Domain not found.", "error")
        return redirect(url_for("domains.domains_list"))

    query = sanitize_input(request.form.get("query", ""))
    location = sanitize_input(request.form.get("location", ""))

    if not query:
        flash("Search query is required.", "error")
        return redirect(url_for("domains.domains_prospects", domain_id=domain_id))

    result = fetch_and_save_businesses(query, location)
    if result is None:
        flash("Failed to fetch businesses — check your API key or network.", "error")
        return redirect(url_for("domains.domains_prospects", domain_id=domain_id))

    # Load all businesses matching the query from DB and annotate
    conn = sqlite3.connect("businesses.db")
    conn.row_factory = sqlite3.Row
    businesses = conn.execute("SELECT * FROM businesses ORDER BY name").fetchall()
    conn.close()

    pitched_ids = get_pitched_business_ids(domain_id)
    prospects = []
    for b in businesses:
        b_dict = dict(b)
        b_dict["weak_website"] = is_weak_website(b["website"])
        b_dict["already_pitched"] = b["id"] in pitched_ids
        prospects.append(b_dict)

    weak_count = sum(1 for p in prospects if not p["website"] or p["weak_website"])
    analysis = analyze_domain(domain["domain"])
    if domain["industry"]:
        analysis["industry"] = domain["industry"]
    if domain["location"]:
        analysis["location"] = domain["location"]
    coord_hint = CITY_COORDS.get(analysis.get("location", ""), "")

    flash(f"Found {len(prospects)} businesses. {weak_count} have no/weak website — ideal targets.", "info")
    return render_template(
        "domain_prospects.html",
        domain=domain,
        analysis=analysis,
        coord_hint=coord_hint,
        prospects=prospects,
        weak_count=weak_count,
    )


@domains_bp.route("/domains/<int:domain_id>/pitch-all", methods=["POST"])
@login_required
def domains_pitch_all(domain_id):
    domain = get_domain(domain_id)
    if not domain:
        flash("Domain not found.", "error")
        return redirect(url_for("domains.domains_list"))

    business_ids = request.form.getlist("business_ids")
    if not business_ids:
        flash("No businesses selected.", "error")
        return redirect(url_for("domains.domains_prospects", domain_id=domain_id))

    import sqlite3
    conn = sqlite3.connect("businesses.db")
    conn.row_factory = sqlite3.Row

    sent, skipped = 0, 0
    for bid in business_ids:
        try:
            business = conn.execute("SELECT * FROM businesses WHERE id=?", (int(bid),)).fetchone()
        except (ValueError, Exception):
            continue
        if not business:
            continue

        to_email = build_recipient_email(business["website"])
        if not to_email:
            skipped += 1
            continue

        pitch = generate_pitch_email(domain["domain"], business["name"], domain["asking_price"] or 0)
        send_email(to_email, pitch["subject"], pitch["body"])
        record_pitch(domain_id, business["id"])
        sent += 1

    conn.close()

    if sent > 0:
        update_domain_status(domain_id, "pitched")

    msg = f"Pitch emails sent to {sent} business(es)."
    if skipped:
        msg += f" {skipped} skipped (no valid email address)."
    flash(msg, "success")
    return redirect(url_for("domains.domains_prospects", domain_id=domain_id))


@domains_bp.route("/domains/<int:domain_id>/sold", methods=["POST"])
@login_required
def domains_mark_sold(domain_id):
    domain = get_domain(domain_id)
    if domain:
        update_domain_status(domain_id, "sold")
        flash(f"🎉 {domain['domain']} marked as sold!", "success")
    return redirect(url_for("domains.domains_list"))


@domains_bp.route("/domains/<int:domain_id>/delete", methods=["POST"])
@login_required
def domains_delete(domain_id):
    domain = get_domain(domain_id)
    if domain:
        delete_domain(domain_id)
        flash(f"Domain '{domain['domain']}' deleted.", "success")
    return redirect(url_for("domains.domains_list"))


@domains_bp.route("/domains/<int:domain_id>/preview-pitch")
@login_required
def domains_preview_pitch(domain_id):
    domain = get_domain(domain_id)
    if not domain:
        flash("Domain not found.", "error")
        return redirect(url_for("domains.domains_list"))
    pitch = generate_pitch_email(domain["domain"], "{business_name}", domain["asking_price"] or 0)
    flash(f"Subject: {pitch['subject']}\n\n{pitch['body']}", "info")
    return redirect(url_for("domains.domains_prospects", domain_id=domain_id))
