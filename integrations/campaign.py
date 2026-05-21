"""
Full automated campaign runner.

Flow per domain:
  1. Analyse domain → build Google Places search query
  2. Fetch matching businesses (Google Places API)
  3. For each business with no/weak website → search Apollo for decision-makers
  4. Send pitch emails to every contact that has an email address
  5. Return a summary dict

Also provides:
  - run_all_campaigns()  — runs run_campaign() for every active (non-sold) domain
  - send_followups()     — sends follow-up emails to contacts pitched >7 days ago
"""

import logging
import sqlite3
from datetime import datetime
from urllib.parse import urlparse

from business_outreach import fetch_and_save_businesses
from database.manage_contacts import (
    add_contacts, get_all_contacts_for_domain, mark_contact_pitched,
)
from database.manage_domains import (
    get_all_domains, get_domain, get_pitched_business_ids,
    record_pitch, update_domain_status,
)
from domain_analyzer import analyze_domain, generate_pitch_email, is_weak_website
from integrations.ai_generator import generate_personalized_pitch, score_lead
from integrations.apollo_connector import search_decision_makers
from outreach.email_sender import send_email

logger = logging.getLogger(__name__)

# Minimal city → lat,lng lookup (mirrors domain_routes.CITY_COORDS)
_CITY_COORDS = {
    "Dubai": "25.2048,55.2708", "London": "51.5074,-0.1278",
    "New York": "40.7128,-74.0060", "Los Angeles": "34.0522,-118.2437",
    "Paris": "48.8566,2.3522", "Tokyo": "35.6762,139.6503",
    "Sydney": "-33.8688,151.2093", "Singapore": "1.3521,103.8198",
    "Toronto": "43.6532,-79.3832", "Berlin": "52.5200,13.4050",
    "Mumbai": "19.0760,72.8777", "São Paulo": "-23.5505,-46.6333",
    "Chicago": "41.8781,-87.6298", "Miami": "25.7617,-80.1918",
    "San Francisco": "37.7749,-122.4194", "Seattle": "47.6062,-122.3321",
}


def _extract_domain(website: str) -> str | None:
    """Return bare domain from a website URL, or None."""
    if not website:
        return None
    if "://" not in website:
        website = "http://" + website
    netloc = urlparse(website).netloc.replace("www.", "").strip()
    return netloc or None


def run_campaign(domain_id: int) -> dict:
    """
    Run a full outreach campaign for one domain.

    Returns a result dict with keys:
      domain, businesses_fetched, weak_website_count,
      contacts_found, emails_sent, errors, timestamp
    """
    result = {
        "domain_id": domain_id,
        "domain": "",
        "businesses_fetched": 0,
        "weak_website_count": 0,
        "contacts_found": 0,
        "emails_sent": 0,
        "errors": [],
        "timestamp": datetime.utcnow().isoformat(),
    }

    domain = get_domain(domain_id)
    if not domain:
        result["errors"].append(f"Domain {domain_id} not found")
        return result

    result["domain"] = domain["domain"]
    analysis = analyze_domain(domain["domain"])
    if domain["industry"]:
        analysis["industry"] = domain["industry"]
    if domain["location"]:
        analysis["location"] = domain["location"]

    query = analysis["search_query"]
    location = _CITY_COORDS.get(analysis.get("location", ""), "")

    # Step 1: Fetch businesses
    businesses = fetch_and_save_businesses(query, location)
    if businesses is None:
        result["errors"].append("Google Places fetch failed — check GOOGLE_API_KEY")
    else:
        result["businesses_fetched"] = len(businesses)

    # Step 2: Process all businesses in DB
    conn = sqlite3.connect("businesses.db")
    conn.row_factory = sqlite3.Row
    all_biz = conn.execute("SELECT * FROM businesses ORDER BY name").fetchall()
    conn.close()

    pitched_ids = get_pitched_business_ids(domain_id)

    for b in all_biz:
        if b["id"] in pitched_ids:
            continue
        if b["website"] and not is_weak_website(b["website"]):
            continue  # skip businesses with proper websites

        result["weak_website_count"] += 1

        # Step 3: Find decision-makers via Apollo
        people, error = search_decision_makers(
            b["name"], domain=_extract_domain(b["website"] or "")
        )
        if error:
            result["errors"].append(f"Apollo '{b['name']}': {error}")
        elif people:
            # Score each lead before saving
            for p in people:
                p["lead_score"] = score_lead(
                    business_name=b["name"],
                    website=b["website"] or "",
                    is_weak=is_weak_website(b["website"] or ""),
                    contact_title=p.get("title", ""),
                    industry=analysis.get("industry", ""),
                    domain=domain["domain"],
                )
            add_contacts(domain_id, b["id"], people)
            result["contacts_found"] += len(people)

    # Step 4: Send pitches to contacts with emails
    contacts_map = get_all_contacts_for_domain(domain_id)
    conn = sqlite3.connect("businesses.db")
    conn.row_factory = sqlite3.Row

    for business_id, contacts in contacts_map.items():
        biz = conn.execute(
            "SELECT name FROM businesses WHERE id=?", (business_id,)
        ).fetchone()
        biz_name = biz["name"] if biz else "there"

        for c in contacts:
            if c.get("pitched") or not c.get("email"):
                continue
            first = (c["name"] or "").split()[0] or "there"
            # Try AI-personalized pitch first; fall back to template
            ai_pitch = generate_personalized_pitch(
                domain=domain["domain"],
                asking_price=domain["asking_price"] or 0,
                contact_name=c.get("name", ""),
                contact_title=c.get("title", ""),
                business_name=biz_name,
                business_website="",
                industry=analysis.get("industry", ""),
            )
            pitch = ai_pitch or generate_pitch_email(
                domain["domain"], first, domain["asking_price"] or 0
            )
            try:
                send_email(c["email"], pitch["subject"], pitch["body"])
                mark_contact_pitched(c["id"])
                record_pitch(domain_id, business_id)
                result["emails_sent"] += 1
            except Exception as e:
                result["errors"].append(f"Email failed ({c['email']}): {e}")

    conn.close()

    if result["emails_sent"] > 0:
        update_domain_status(domain_id, "pitched")

    logger.info(
        "Campaign %s: %d fetched, %d weak, %d contacts, %d sent, %d errors",
        domain["domain"], result["businesses_fetched"], result["weak_website_count"],
        result["contacts_found"], result["emails_sent"], len(result["errors"]),
    )
    return result


def run_all_campaigns() -> list:
    """Run campaigns for all active (non-sold) domains."""
    results = []
    for d in get_all_domains():
        if d["status"] != "sold":
            results.append(run_campaign(d["id"]))
    return results


def send_followups() -> int:
    """
    Send follow-up emails to contacts pitched more than 7 days ago
    that have not yet received a follow-up.
    Returns the number of follow-up emails sent.
    """
    sent = 0
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.row_factory = sqlite3.Row
        stale = conn.execute("""
            SELECT dc.id, dc.name, dc.email, dc.domain_id,
                   d.domain, d.asking_price
            FROM domain_contacts dc
            JOIN domains d ON dc.domain_id = d.id
            WHERE dc.pitched = 1
              AND dc.followup_sent = 0
              AND dc.email IS NOT NULL AND dc.email != ''
              AND dc.pitched_at < datetime('now', '-7 days')
        """).fetchall()
        conn.close()
        conn = None

        for c in stale:
            first = (c["name"] or "").split()[0] or "there"
            subject = f"Quick follow-up — {c['domain']}"
            body = (
                f"Hi {first},\n\n"
                f"I wanted to follow up on my earlier message about {c['domain']}.\n\n"
                f"This domain could be a strong fit for your brand. "
                f"I'm still open to offers and happy to discuss.\n\n"
                f"Would you have 10 minutes for a quick chat?\n\n"
                f"Best regards"
            )
            try:
                send_email(c["email"], subject, body)
                conn2 = sqlite3.connect("businesses.db")
                conn2.execute(
                    "UPDATE domain_contacts SET followup_sent=1 WHERE id=?",
                    (c["id"],),
                )
                conn2.commit()
                conn2.close()
                sent += 1
                logger.info("Follow-up sent to %s for %s", c["email"], c["domain"])
            except Exception as e:
                logger.error("Follow-up failed for %s: %s", c["email"], e)
    except Exception as e:
        logger.error("send_followups error: %s", e)
        if conn:
            conn.close()
    return sent
