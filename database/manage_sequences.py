"""CRUD helpers for email_sequences, sequence_steps, sequence_enrollments."""
import sqlite3
from datetime import datetime, timedelta


def create_sequence(name: str, description: str = "") -> int | None:
    """Create a new sequence. Returns new id or None on duplicate."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        cur = conn.execute(
            "INSERT INTO email_sequences (name, description) VALUES (?, ?)",
            (name.strip(), description.strip()),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        if conn: conn.close()


def get_all_sequences() -> list:
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.row_factory = sqlite3.Row
        return conn.execute(
            """SELECT s.*,
                      COUNT(DISTINCT st.id)  AS step_count,
                      COUNT(DISTINCT e.id)   AS enrolled_count
               FROM email_sequences s
               LEFT JOIN sequence_steps st ON st.sequence_id = s.id
               LEFT JOIN sequence_enrollments e ON e.sequence_id = s.id
               GROUP BY s.id ORDER BY s.created_at DESC"""
        ).fetchall()
    except sqlite3.Error as e:
        print(f"manage_sequences error: {e}"); return []
    finally:
        if conn: conn.close()


def get_sequence(seq_id: int):
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT * FROM email_sequences WHERE id=?", (seq_id,)
        ).fetchone()
    except sqlite3.Error as e:
        print(f"manage_sequences error: {e}"); return None
    finally:
        if conn: conn.close()


def get_steps(seq_id: int) -> list:
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT * FROM sequence_steps WHERE sequence_id=? ORDER BY step_number",
            (seq_id,),
        ).fetchall()
    except sqlite3.Error as e:
        print(f"manage_sequences error: {e}"); return []
    finally:
        if conn: conn.close()


def add_step(seq_id: int, step_number: int, delay_days: int,
             subject_template: str, body_template: str) -> bool:
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.execute(
            """INSERT INTO sequence_steps
               (sequence_id, step_number, delay_days, subject_template, body_template)
               VALUES (?, ?, ?, ?, ?)""",
            (seq_id, step_number, delay_days, subject_template, body_template),
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"manage_sequences error: {e}"); return False
    finally:
        if conn: conn.close()


def delete_step(step_id: int) -> None:
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.execute("DELETE FROM sequence_steps WHERE id=?", (step_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"manage_sequences error: {e}")
    finally:
        if conn: conn.close()


def delete_sequence(seq_id: int) -> None:
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.execute("DELETE FROM email_sequences WHERE id=?", (seq_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"manage_sequences error: {e}")
    finally:
        if conn: conn.close()


def enroll_contact(seq_id: int, contact_id: int, domain_id: int) -> bool:
    """Enroll a contact in a sequence. Sets next_send_at to now (step 1 sends immediately)."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.execute(
            """INSERT OR IGNORE INTO sequence_enrollments
               (sequence_id, contact_id, domain_id, current_step, next_send_at)
               VALUES (?, ?, ?, 1, datetime('now'))""",
            (seq_id, contact_id, domain_id),
        )
        conn.commit()
        return conn.execute("SELECT changes()").fetchone()[0] > 0
    except sqlite3.Error as e:
        print(f"manage_sequences error: {e}"); return False
    finally:
        if conn: conn.close()


def get_due_enrollments() -> list:
    """Return enrollments due to have their next step sent."""
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        conn.row_factory = sqlite3.Row
        return conn.execute(
            """SELECT e.*,
                      dc.name AS contact_name, dc.email AS contact_email,
                      dc.title AS contact_title,
                      d.domain AS domain_name, d.asking_price,
                      b.name AS business_name
               FROM sequence_enrollments e
               JOIN domain_contacts dc ON dc.id = e.contact_id
               JOIN domains d ON d.id = e.domain_id
               LEFT JOIN businesses b ON b.id = dc.business_id
               WHERE e.completed = 0
                 AND e.next_send_at <= datetime('now')"""
        ).fetchall()
    except sqlite3.Error as e:
        print(f"manage_sequences error: {e}"); return []
    finally:
        if conn: conn.close()


def advance_enrollment(enrollment_id: int, next_step: int,
                       delay_days: int, completed: bool = False) -> None:
    conn = None
    try:
        conn = sqlite3.connect("businesses.db")
        if completed:
            conn.execute(
                "UPDATE sequence_enrollments SET completed=1 WHERE id=?",
                (enrollment_id,),
            )
        else:
            next_send = datetime.utcnow() + timedelta(days=delay_days)
            conn.execute(
                """UPDATE sequence_enrollments
                   SET current_step=?, next_send_at=? WHERE id=?""",
                (next_step, next_send.strftime("%Y-%m-%d %H:%M:%S"), enrollment_id),
            )
        conn.commit()
    except sqlite3.Error as e:
        print(f"manage_sequences error: {e}")
    finally:
        if conn: conn.close()
