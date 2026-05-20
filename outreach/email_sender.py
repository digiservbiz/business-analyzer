
import os
import random
import smtplib
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from urllib.parse import urlparse


def get_email_template(name=None):
    """Fetches an email template from the database, either by name or randomly."""
    conn = None
    try:
        conn = sqlite3.connect('businesses.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if name:
            c.execute("SELECT subject, body FROM email_templates WHERE name = ?", (name,))
            template = c.fetchone()
            if not template:
                print(f"Error: Template with name '{name}' not found.")
                return None
            return dict(template)
        else:
            c.execute("SELECT subject, body FROM email_templates")
            templates = c.fetchall()
            return dict(random.choice(templates)) if templates else None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()


def build_recipient_email(website):
    """
    Derive a best-guess contact email from a business website URL.
    Returns None if the website is empty or unparseable.
    """
    if not website:
        return None
    try:
        parsed = urlparse(website if website.startswith(("http://", "https://")) else f"https://{website}")
        domain = parsed.netloc or parsed.path
        # Strip leading www.
        domain = domain.lstrip("www.")
        if domain:
            return f"contact@{domain}"
    except Exception:
        pass
    return None


def send_email(to_email, subject, body, report_path=None):
    """
    Sends an email via SMTP if credentials are configured, otherwise simulates.

    Required env vars for real sending:
        EMAIL_HOST   — SMTP server hostname (e.g. smtp.gmail.com)
        EMAIL_PORT   — SMTP port (465 for SSL, 587 for STARTTLS)
        EMAIL_USER   — Sender email address
        EMAIL_PASS   — Sender password / app password
        EMAIL_FROM   — Display name + address (optional, defaults to EMAIL_USER)
    """
    host = os.getenv("EMAIL_HOST")
    port = int(os.getenv("EMAIL_PORT", 465))
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")

    if not all([host, user, password]):
        _simulate_email(to_email, subject, body, report_path)
        return False

    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = os.getenv("EMAIL_FROM", user)
        msg["To"] = to_email
        msg.attach(MIMEText(body, "plain"))

        if report_path:
            with open(report_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(report_path))
                part["Content-Disposition"] = f'attachment; filename="{os.path.basename(report_path)}"'
                msg.attach(part)

        if port == 587:
            with smtplib.SMTP(host, port, timeout=10) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(user, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP_SSL(host, port, timeout=10) as smtp:
                smtp.login(user, password)
                smtp.send_message(msg)

        print(f"[email] Sent to {to_email} — subject: {subject}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("[email] Authentication failed — check EMAIL_USER and EMAIL_PASS.")
        _simulate_email(to_email, subject, body, report_path)
        return False
    except smtplib.SMTPException as e:
        print(f"[email] SMTP error: {e}")
        _simulate_email(to_email, subject, body, report_path)
        return False
    except OSError as e:
        print(f"[email] Connection error ({host}:{port}): {e}")
        _simulate_email(to_email, subject, body, report_path)
        return False


def _simulate_email(to_email, subject, body, report_path=None):
    """Prints email content to console when SMTP is not configured."""
    print("\n--- SIMULATED EMAIL (configure EMAIL_* env vars to send for real) ---")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    if report_path:
        print(f"Attachment: {report_path}")
    print("--- END SIMULATED EMAIL ---\n")
