
import os
import random
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

def get_email_template(name=None):
    """Fetches an email template from the database, either by name or randomly."""
    try:
        conn = sqlite3.connect('businesses.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if name:
            c.execute("SELECT subject, body FROM email_templates WHERE name = ?", (name,))
            template = c.fetchone()
            if not template:
                print(f"Error: Template with name ''{name}'' not found.")
                return None
            return template
        else:
            c.execute("SELECT subject, body FROM email_templates")
            templates = c.fetchall()
            return random.choice(templates) if templates else None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def send_email(to_email, subject, body, report_path=None):
    """Simulates sending an email by printing the content to the console."""
    print("\n--- SIMULATING EMAIL --- ")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print("Body:")
    print(body)
    if report_path:
        print(f"Attachment: {report_path}")
    print("--- END SIMULATING EMAIL ---\n")
    # The original email sending code is commented out below.
    # To enable actual email sending, uncomment the code and configure your
    # environment variables (EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS).
    # import smtplib
    # msg = MIMEMultipart()
    # msg['Subject'] = subject
    # msg['From'] = os.getenv("EMAIL_USER")
    # msg['To'] = to_email
    # msg.attach(MIMEText(body))
    # if report_path:
    #     with open(report_path, "rb") as file:
    #         part = MIMEApplication(file.read(), Name="report.pdf")
    #         part['Content-Disposition'] = f'attachment; filename="{os.path.basename(report_path)}"'
    #         msg.attach(part)
    # with smtplib.SMTP_SSL(os.getenv("EMAIL_HOST"), int(os.getenv("EMAIL_PORT", 465))) as smtp:
    #     smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
    #     smtp.send_message(msg)
