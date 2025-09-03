
import smtplib
import os
import random
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 465))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def get_random_email_template():
    """Fetches a random email template from the database using sqlite3."""
    try:
        conn = sqlite3.connect('businesses.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT subject, body FROM email_templates")
        templates = c.fetchall()
        conn.close()
        return random.choice(templates) if templates else None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

def send_email(to_email, report_path):
    template = get_random_email_template()

    if template:
        subject = template['subject']
        body = template['body']
    else:
        subject = "Free Online Business Report"
        body = "Hi! Here's a free report analyzing your business's online presence."

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = to_email

    msg.attach(MIMEText(body))

    with open(report_path, "rb") as file:
        part = MIMEApplication(file.read(), Name="report.pdf")
        part['Content-Disposition'] = 'attachment; filename="report.pdf"'
        msg.attach(part)

    with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)
