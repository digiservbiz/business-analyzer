"""
Company news monitor — fetches Google News RSS for prospect companies.
Scores relevance with Claude and stores alerts in news_alerts table.
"""
import logging
import os
import sqlite3
import xml.etree.ElementTree as ET
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

BUYING_SIGNALS = [
    "expansion", "new location", "new office", "opens", "launched", "funding",
    "raised", "investment", "series a", "series b", "growth", "hiring", "acquired",
    "rebranding", "renovation", "partnership", "new branch",
]


def _fetch_news(company_name: str, max_results: int = 5) -> list:
    """Fetch Google News RSS for a company. Returns list of (headline, url, source) tuples."""
    query = quote(f'"{company_name}"')
    url = f"https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en"
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return []
        root = ET.fromstring(resp.content)
        items = []
        for item in root.findall(".//item")[:max_results]:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            source = item.findtext("source", "")
            items.append((title, link, source))
        return items
    except Exception as exc:
        logger.debug("News fetch error for %s: %s", company_name, exc)
        return []


def _score_relevance(headline: str) -> int:
    """Score 0-100 based on buying signal keywords in headline."""
    headline_lower = headline.lower()
    score = 0
    for signal in BUYING_SIGNALS:
        if signal in headline_lower:
            score += 20
    return min(score, 100)


def _classify_with_ai(company_name: str, headline: str) -> int:
    """Use Claude to score relevance as a buying signal (0-100). Falls back to keyword score."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return _score_relevance(headline)
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": (
                    f"Company: {company_name}\n"
                    f"News headline: {headline}\n\n"
                    "Score 0-100: how likely is this news a buying signal "
                    "(expansion, funding, growth = high score; unrelated news = low score). "
                    "Reply with only a number."
                ),
            }],
        )
        return min(100, max(0, int(resp.content[0].text.strip())))
    except Exception:
        return _score_relevance(headline)


def _already_stored(conn, business_name: str, headline: str) -> bool:
    """Prevent duplicate alerts for the same headline."""
    row = conn.execute(
        "SELECT id FROM news_alerts WHERE business_name=? AND headline=?",
        (business_name, headline),
    ).fetchone()
    return row is not None


def check_news() -> int:
    """
    Fetch news for all prospect businesses. Store alerts with relevance >= 40.
    Returns number of new alerts stored.
    """
    try:
        conn = sqlite3.connect("businesses.db")
        conn.row_factory = sqlite3.Row
        businesses = conn.execute(
            "SELECT DISTINCT name FROM businesses ORDER BY name"
        ).fetchall()
        conn.close()
    except sqlite3.Error as exc:
        logger.error("DB error loading businesses: %s", exc)
        return 0

    if not businesses:
        logger.debug("No businesses to monitor for news")
        return 0

    new_alerts = 0
    conn = sqlite3.connect("businesses.db")

    for biz in businesses:
        name = biz["name"]
        articles = _fetch_news(name)
        for headline, url, source in articles:
            if _already_stored(conn, name, headline):
                continue
            score = _classify_with_ai(name, headline)
            if score >= 40:
                conn.execute(
                    """INSERT INTO news_alerts
                       (business_name, headline, url, source, relevance_score)
                       VALUES (?, ?, ?, ?, ?)""",
                    (name, headline, url, source, score),
                )
                conn.commit()
                logger.info("News alert stored: %s — %s (score=%d)", name, headline[:60], score)
                new_alerts += 1

    conn.close()
    if new_alerts:
        logger.info("News monitor: %d new alerts", new_alerts)
    return new_alerts
