"""Query helpers for the analytics dashboard."""
import sqlite3


def get_summary_stats() -> dict:
    """Return high-level counts across all domains."""
    conn = sqlite3.connect("businesses.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    stats = {
        "total_domains":     c.execute("SELECT COUNT(*) FROM domains").fetchone()[0],
        "total_available":   c.execute("SELECT COUNT(*) FROM domains WHERE status='available'").fetchone()[0],
        "total_pitched":     c.execute("SELECT COUNT(*) FROM domains WHERE status='pitched'").fetchone()[0],
        "total_negotiating": c.execute("SELECT COUNT(*) FROM domains WHERE status='negotiating'").fetchone()[0],
        "total_sold":        c.execute("SELECT COUNT(*) FROM domains WHERE status='sold'").fetchone()[0],
        "total_businesses":  c.execute("SELECT COUNT(*) FROM businesses").fetchone()[0],
        "total_contacts":    c.execute("SELECT COUNT(*) FROM domain_contacts").fetchone()[0],
        "total_emails":      c.execute("SELECT COALESCE(SUM(emails_sent),0) FROM campaign_runs").fetchone()[0],
        "total_replies":     c.execute("SELECT COUNT(*) FROM domain_contacts WHERE replied=1").fetchone()[0],
    }
    conn.close()
    total = stats["total_contacts"]
    stats["reply_rate"] = round(stats["total_replies"] / total * 100, 1) if total else 0.0
    return stats


def get_weekly_pitch_counts(weeks: int = 8) -> list:
    """Return weekly email-sent totals for the last N weeks."""
    conn = sqlite3.connect("businesses.db")
    rows = conn.execute(
        """SELECT strftime('%Y-W%W', ran_at) AS week,
                  SUM(emails_sent) AS total
           FROM campaign_runs
           WHERE ran_at >= datetime('now', ? )
           GROUP BY week
           ORDER BY week""",
        (f"-{weeks * 7} days",),
    ).fetchall()
    conn.close()
    return [{"week": r[0], "total": r[1] or 0} for r in rows]


def get_domain_performance() -> list:
    """Return per-domain performance stats."""
    conn = sqlite3.connect("businesses.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT
               d.domain, d.status, d.asking_price,
               COALESCE(SUM(cr.emails_sent), 0)                             AS emails_sent,
               COUNT(DISTINCT dc.id)                                         AS contact_count,
               COUNT(DISTINCT CASE WHEN dc.replied = 1 THEN dc.id END)       AS reply_count
           FROM domains d
           LEFT JOIN campaign_runs cr ON cr.domain_id = d.id
           LEFT JOIN domain_contacts dc ON dc.domain_id = d.id
           GROUP BY d.id
           ORDER BY emails_sent DESC"""
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["reply_rate"] = (
            round(d["reply_count"] / d["contact_count"] * 100, 1)
            if d["contact_count"] else 0.0
        )
        result.append(d)
    return result
