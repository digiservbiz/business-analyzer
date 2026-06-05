import sqlite3


def get_recent_alerts(limit=50, actioned=None):
    """Return recent news alerts. Pass actioned=0 for unread only."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.row_factory = sqlite3.Row
        if actioned is not None:
            return conn.execute(
                """SELECT * FROM news_alerts WHERE actioned=?
                   ORDER BY detected_at DESC LIMIT ?""",
                (actioned, limit),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM news_alerts ORDER BY detected_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()


def mark_actioned(alert_id):
    """Mark a news alert as actioned (user has seen/acted on it)."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.execute("UPDATE news_alerts SET actioned=1 WHERE id=?", (alert_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


def get_alert_count(actioned=0):
    """Return count of alerts (unread by default)."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        return conn.execute(
            "SELECT COUNT(*) FROM news_alerts WHERE actioned=?", (actioned,)
        ).fetchone()[0]
    except sqlite3.Error:
        return 0
    finally:
        if conn:
            conn.close()
