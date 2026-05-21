"""CRUD helpers for domain_contacts table."""
import sqlite3


def add_contacts(domain_id, business_id, contacts):
    """
    Replace existing contacts for (domain_id, business_id) with new list.
    Each contact dict must have: name, title, email, linkedin_url, source.
    Returns True on success.
    """
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.execute(
            "DELETE FROM domain_contacts WHERE domain_id=? AND business_id=?",
            (domain_id, business_id),
        )
        for c in contacts:
            conn.execute(
                """INSERT INTO domain_contacts
                   (domain_id, business_id, name, title, email, linkedin_url, source, lead_score)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (domain_id, business_id,
                 c.get("name", ""), c.get("title", ""),
                 c.get("email", ""), c.get("linkedin_url", ""),
                 c.get("source", "apollo"), c.get("lead_score", 0)),
            )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"manage_contacts error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_all_contacts_for_domain(domain_id):
    """
    Return a dict keyed by business_id -> list of contact dicts for a domain.
    """
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM domain_contacts WHERE domain_id=? ORDER BY business_id, id",
            (domain_id,),
        ).fetchall()
        result = {}
        for r in rows:
            bid = r["business_id"]
            result.setdefault(bid, []).append(dict(r))
        return result
    except sqlite3.Error as e:
        print(f"manage_contacts error: {e}")
        return {}
    finally:
        if conn:
            conn.close()


def get_contact(contact_id):
    """Return a single contact row by id."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT * FROM domain_contacts WHERE id=?", (contact_id,)
        ).fetchone()
    except sqlite3.Error as e:
        print(f"manage_contacts error: {e}")
        return None
    finally:
        if conn:
            conn.close()


def mark_contact_pitched(contact_id):
    """Set pitched=1 on a contact."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.execute(
            "UPDATE domain_contacts SET pitched=1, pitched_at=CURRENT_TIMESTAMP WHERE id=?",
            (contact_id,),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"manage_contacts error: {e}")
    finally:
        if conn:
            conn.close()


def mark_contact_replied(contact_id):
    """Mark a contact as having replied."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.execute(
            "UPDATE domain_contacts SET replied=1, replied_at=CURRENT_TIMESTAMP WHERE id=?",
            (contact_id,),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"manage_contacts error: {e}")
    finally:
        if conn:
            conn.close()


def save_reply_draft(contact_id, draft_text):
    """Store an AI-generated reply draft for a contact."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.execute(
            "UPDATE domain_contacts SET reply_draft=? WHERE id=?",
            (draft_text, contact_id),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"manage_contacts error: {e}")
    finally:
        if conn:
            conn.close()


def get_replied_contacts(domain_id):
    """Return all contacts for a domain that have replied."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.row_factory = sqlite3.Row
        return conn.execute(
            """SELECT dc.*, b.name as business_name, b.website as business_website
               FROM domain_contacts dc
               LEFT JOIN businesses b ON dc.business_id = b.id
               WHERE dc.domain_id=? AND dc.replied=1
               ORDER BY dc.replied_at DESC""",
            (domain_id,),
        ).fetchall()
    except sqlite3.Error as e:
        print(f"manage_contacts error: {e}")
        return []
    finally:
        if conn:
            conn.close()
