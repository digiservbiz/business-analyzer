"""
IMAP inbox monitor — detects replies from previously pitched contacts.

Requires EMAIL_HOST, EMAIL_USER, EMAIL_PASS env vars (same as SMTP sender).
Marks domain_contacts.replied=1 when a matching sender is found.
"""
import email as email_lib
import imaplib
import logging
import os
import sqlite3

logger = logging.getLogger(__name__)


def _extract_sender(from_header: str) -> str:
    """Return bare email address from 'Name <email>' or 'email' header."""
    from_header = from_header.strip()
    if "<" in from_header and ">" in from_header:
        return from_header.split("<")[-1].rstrip(">").strip().lower()
    return from_header.lower()


def check_replies() -> int:
    """
    Connect to IMAP inbox, find replies from pitched contacts, mark them.
    Returns number of new replies detected.
    """
    host = os.getenv("EMAIL_HOST", "").strip()
    user = os.getenv("EMAIL_USER", "").strip()
    password = os.getenv("EMAIL_PASS", "").strip()

    if not all([host, user, password]):
        logger.debug("IMAP check skipped — EMAIL_HOST/USER/PASS not configured")
        return 0

    try:
        # Load pitched contact emails from DB
        conn = sqlite3.connect("businesses.db")
        conn.row_factory = sqlite3.Row
        pitched = conn.execute(
            """SELECT id, email FROM domain_contacts
               WHERE pitched=1 AND replied=0
               AND email IS NOT NULL AND email != ''"""
        ).fetchall()
        conn.close()

        if not pitched:
            return 0

        pitched_map = {c["email"].lower(): c["id"] for c in pitched}

        # Connect via IMAP SSL
        mail = imaplib.IMAP4_SSL(host, 993)
        mail.login(user, password)
        mail.select("INBOX")

        # Search last 14 days to catch delayed replies
        _, data = mail.search(None, "SINCE", "14-days-ago")
        msg_ids = data[0].split() if data[0] else []

        new_replies = 0
        for mid in msg_ids:
            try:
                _, msg_data = mail.fetch(mid, "(RFC822.HEADER)")
                raw_headers = msg_data[0][1]
                msg = email_lib.message_from_bytes(raw_headers)
                sender = _extract_sender(msg.get("From", ""))

                if sender in pitched_map:
                    contact_id = pitched_map[sender]
                    upd = sqlite3.connect("businesses.db")
                    upd.execute(
                        """UPDATE domain_contacts
                           SET replied=1, replied_at=CURRENT_TIMESTAMP
                           WHERE id=?""",
                        (contact_id,),
                    )
                    upd.commit()
                    upd.close()
                    logger.info("Reply detected from %s (contact id=%d)", sender, contact_id)
                    new_replies += 1
            except Exception as exc:
                logger.debug("Error processing message %s: %s", mid, exc)

        mail.logout()
        if new_replies:
            logger.info("IMAP: %d new replies detected", new_replies)
        return new_replies

    except imaplib.IMAP4.error as exc:
        logger.warning("IMAP auth/connection error: %s", exc)
        return 0
    except Exception as exc:
        logger.error("check_replies error: %s", exc)
        return 0
