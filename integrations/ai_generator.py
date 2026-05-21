"""
AI-powered features using Claude API (Anthropic).

Provides:
  - generate_personalized_pitch()  — Claude-written pitch emails
  - score_lead()                   — 0-100 lead score based on signals
  - draft_reply()                  — Draft counter-offer when buyer replies

Requires ANTHROPIC_API_KEY in .env.
All functions gracefully return None/fallback if key is missing.
"""
import logging
import os

logger = logging.getLogger(__name__)

_INVALID_KEYS = {"", "your_anthropic_api_key", "YOUR_ANTHROPIC_API_KEY"}
# Use Haiku for cost efficiency on high-volume email generation
_MODEL = "claude-haiku-4-5-20251001"


def _get_client():
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if api_key in _INVALID_KEYS:
        return None
    try:
        from anthropic import Anthropic
        return Anthropic(api_key=api_key)
    except ImportError:
        logger.warning("anthropic package not installed — AI features disabled")
        return None
    except Exception as exc:
        logger.warning("Anthropic client init failed: %s", exc)
        return None


def generate_personalized_pitch(
    domain: str,
    asking_price: float,
    contact_name: str,
    contact_title: str,
    business_name: str,
    business_website: str,
    industry: str,
) -> dict | None:
    """
    Generate a personalised pitch email via Claude.
    Returns {"subject": str, "body": str, "ai_generated": True}
    or None if API key not configured or call fails.
    """
    client = _get_client()
    if not client:
        return None

    first = (contact_name or "").split()[0] or "there"
    price_str = f"${asking_price:,.0f}" if asking_price and asking_price > 0 else "a competitive price"
    site_note = (
        f"Their current website: {business_website}"
        if business_website
        else "They currently have no website."
    )

    prompt = (
        f"You are a professional domain broker. Write a short cold outreach email.\n\n"
        f"Domain for sale: {domain}\n"
        f"Asking price: {price_str}\n"
        f"Recipient: {contact_name} ({contact_title}) at {business_name}\n"
        f"{site_note}\n"
        f"Industry: {industry}\n\n"
        f"Requirements:\n"
        f"- Address them by first name ({first})\n"
        f"- Explain specifically why {domain} suits {business_name}\n"
        f"- If they have no/weak website, mention how this domain could anchor their online presence\n"
        f"- Mention the price naturally\n"
        f"- Keep it under 120 words\n"
        f"- Tone: confident, brief, human — not salesy\n"
        f"- End with a soft call to action\n\n"
        f"Respond in this exact format (no extra text):\n"
        f"SUBJECT: <subject line>\n\n"
        f"<email body>"
    )

    try:
        resp = client.messages.create(
            model=_MODEL,
            max_tokens=350,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        # Parse SUBJECT: line
        if text.startswith("SUBJECT:"):
            parts = text.split("\n\n", 1)
            subject = parts[0].replace("SUBJECT:", "").strip()
            body = parts[1].strip() if len(parts) > 1 else text
        else:
            subject = f"A premium domain opportunity for {business_name}"
            body = text
        return {"subject": subject, "body": body, "ai_generated": True}
    except Exception as exc:
        logger.warning("AI pitch generation failed: %s", exc)
        return None


def score_lead(
    business_name: str,
    website: str,
    is_weak: bool,
    contact_title: str,
    industry: str,
    domain: str,
) -> int:
    """
    Score a lead 0–100. Higher = better buying probability.

    Scoring breakdown:
      Website signals  : 0–40 pts
      Decision-maker   : 0–30 pts
      Industry match   : 0–20 pts
      Name match       : 0–10 pts
    """
    score = 0

    # Website signals
    if not website:
        score += 40
    elif is_weak:
        score += 25
    else:
        score += 5

    # Decision-maker seniority
    title = (contact_title or "").lower()
    if any(t in title for t in ("ceo", "owner", "founder", "president", "proprietor")):
        score += 30
    elif any(t in title for t in ("director", " vp ", "vice president", "head of")):
        score += 20
    elif any(t in title for t in ("manager", "marketing", "digital")):
        score += 10

    # Industry–domain keyword overlap
    domain_clean = domain.lower().replace("-", " ").replace(".", " ")
    for word in (industry or "").lower().split():
        if len(word) > 3 and word in domain_clean:
            score += 20
            break

    # Business name–domain keyword overlap
    for word in business_name.lower().split():
        if len(word) > 3 and word in domain_clean:
            score += 10
            break

    return min(score, 100)


def draft_reply(
    domain: str,
    asking_price: float,
    contact_name: str,
    contact_title: str,
    business_name: str,
) -> str | None:
    """
    Draft a counter-offer / follow-through reply when a buyer responds.
    Returns the draft body string, or None if unavailable.
    """
    client = _get_client()
    if not client:
        return None

    first = (contact_name or "").split()[0] or "there"
    price_str = f"${asking_price:,.0f}" if asking_price and asking_price > 0 else "a competitive price"

    prompt = (
        f"A potential buyer replied to a domain pitch. Write a brief, professional follow-up.\n\n"
        f"Domain: {domain} (asking {price_str})\n"
        f"Buyer: {contact_name} ({contact_title}) at {business_name}\n\n"
        f"The reply was positive/enquiring. Write a short response (under 100 words) that:\n"
        f"- Thanks them for responding\n"
        f"- Offers to answer any questions\n"
        f"- Suggests a brief call or next step\n"
        f"- Reinforces the value of the domain briefly\n"
        f"- Addresses them as {first}\n"
        f"- Is warm, professional, not pushy\n\n"
        f"Return ONLY the email body (no subject line)."
    )

    try:
        resp = client.messages.create(
            model=_MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
    except Exception as exc:
        logger.warning("AI reply draft failed: %s", exc)
        return None
