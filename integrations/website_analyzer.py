"""
AI Website Analyzer — fetches a business website's HTML and uses Claude
to generate a structured analysis: quality score, missing elements, pain points.
Results are cached in domain_contacts.website_analysis (JSON string).
"""
import json
import logging
import os

import requests

logger = logging.getLogger(__name__)


def _fetch_html(url: str) -> str:
    """Fetch page HTML, return first 8000 chars."""
    if not url:
        return ""
    if not url.startswith("http"):
        url = "https://" + url
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        return resp.text[:8000]
    except Exception as exc:
        logger.debug("Website fetch error %s: %s", url, exc)
        return ""


def analyze_website(business_name: str, website_url: str) -> dict:
    """
    Analyze a business website with Claude. Returns dict:
    {
        "score": 0-100,
        "has_contact_page": bool,
        "has_booking": bool,
        "mobile_friendly_signals": bool,
        "missing": ["list", "of", "issues"],
        "pitch_hook": "One sentence why they need your service",
        "error": None or str
    }
    Falls back to a basic dict if no API key or fetch fails.
    """
    default = {
        "score": 0,
        "has_contact_page": False,
        "has_booking": False,
        "mobile_friendly_signals": False,
        "missing": [],
        "pitch_hook": "",
        "error": None,
    }

    if not website_url:
        default["error"] = "No website"
        default["pitch_hook"] = f"{business_name} has no website — ideal prospect."
        return default

    html = _fetch_html(website_url)
    if not html:
        default["error"] = "Could not fetch website"
        return default

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        # Basic keyword analysis without AI
        lower = html.lower()
        default["has_contact_page"] = "contact" in lower
        default["has_booking"] = any(w in lower for w in ["book", "reserve", "appointment", "schedule"])
        default["mobile_friendly_signals"] = "viewport" in lower
        default["score"] = (
            (20 if default["has_contact_page"] else 0) +
            (20 if default["has_booking"] else 0) +
            (20 if default["mobile_friendly_signals"] else 0)
        )
        default["missing"] = [
            k for k, v in {
                "Contact page": default["has_contact_page"],
                "Booking/reservation": default["has_booking"],
                "Mobile viewport": default["mobile_friendly_signals"],
            }.items() if not v
        ]
        return default

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": (
                    f"Analyze this website HTML for business: {business_name}\n"
                    f"URL: {website_url}\n\n"
                    f"HTML snippet:\n{html[:4000]}\n\n"
                    "Return a JSON object with these exact keys:\n"
                    '{"score": 0-100, "has_contact_page": true/false, '
                    '"has_booking": true/false, "mobile_friendly_signals": true/false, '
                    '"missing": ["list of missing elements"], '
                    '"pitch_hook": "one sentence why this business needs digital services"}\n'
                    "Return only valid JSON, no other text."
                ),
            }],
        )
        text = resp.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text)
        for key in default:
            if key not in result:
                result[key] = default[key]
        return result
    except Exception as exc:
        logger.warning("Website analysis error for %s: %s", website_url, exc)
        default["error"] = str(exc)
        return default


def analysis_to_json(analysis: dict) -> str:
    return json.dumps(analysis)


def json_to_analysis(s: str) -> dict:
    try:
        return json.loads(s) if s else {}
    except Exception:
        return {}
