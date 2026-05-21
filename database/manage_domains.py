import sqlite3


def add_domain(domain, keywords, industry, location, asking_price=0, notes=""):
    """Add a new domain to the portfolio."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.execute(
            """INSERT INTO domains (domain, keywords, industry, location, asking_price, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (domain.lower().strip(), keywords, industry, location, asking_price, notes),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_all_domains():
    """Return all domains with pitch counts."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT d.*,
                      COUNT(dp.id) as pitch_count
               FROM domains d
               LEFT JOIN domain_pitches dp ON dp.domain_id = d.id
               GROUP BY d.id
               ORDER BY d.created_at DESC"""
        ).fetchall()
        return rows
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_domain(domain_id):
    """Return a single domain by id."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT * FROM domains WHERE id=?", (domain_id,)
        ).fetchone()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()


def update_domain_status(domain_id, status):
    """Update domain status: available | pitched | sold."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.execute("UPDATE domains SET status=? WHERE id=?", (status, domain_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


def delete_domain(domain_id):
    """Delete a domain and all its pitch records."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.execute("DELETE FROM domains WHERE id=?", (domain_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


def record_pitch(domain_id, business_id):
    """Record that a domain was pitched to a business (ignore duplicates)."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.execute(
            """INSERT OR IGNORE INTO domain_pitches (domain_id, business_id)
               VALUES (?, ?)""",
            (domain_id, business_id),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


def get_pitched_business_ids(domain_id):
    """Return set of business IDs already pitched for this domain."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        rows = conn.execute(
            "SELECT business_id FROM domain_pitches WHERE domain_id=?", (domain_id,)
        ).fetchall()
        return {r[0] for r in rows}
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return set()
    finally:
        if conn:
            conn.close()
