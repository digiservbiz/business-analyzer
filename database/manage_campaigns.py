"""CRUD for campaign_runs table."""
import json
import sqlite3


def log_campaign_run(domain_id, result):
    """Persist a campaign result dict to campaign_runs."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.execute(
            """INSERT INTO campaign_runs
               (domain_id, domain, businesses_fetched, weak_website_count,
                contacts_found, emails_sent, errors)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                domain_id,
                result.get("domain", ""),
                result.get("businesses_fetched", 0),
                result.get("weak_website_count", 0),
                result.get("contacts_found", 0),
                result.get("emails_sent", 0),
                json.dumps(result.get("errors", [])),
            ),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"manage_campaigns error: {e}")
    finally:
        if conn:
            conn.close()


def get_campaign_history(domain_id, limit=10):
    """Return recent campaign runs for a domain, newest first."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.row_factory = sqlite3.Row
        return conn.execute(
            """SELECT * FROM campaign_runs
               WHERE domain_id=?
               ORDER BY ran_at DESC LIMIT ?""",
            (domain_id, limit),
        ).fetchall()
    except sqlite3.Error as e:
        print(f"manage_campaigns error: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_all_recent_campaigns(limit=20):
    """Return the most recent campaign runs across all domains."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT * FROM campaign_runs ORDER BY ran_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    except sqlite3.Error as e:
        print(f"manage_campaigns error: {e}")
        return []
    finally:
        if conn:
            conn.close()
