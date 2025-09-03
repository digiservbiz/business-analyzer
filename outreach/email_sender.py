import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 465))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def send_email(to_email, report_path):
    msg = MIMEMultipart()
    msg['Subject'] = "Free Online Business Report"
    msg['From'] = EMAIL_USER
    msg['To'] = to_email

    text = "Hi! Here's a free report analyzing your business's online presence."
    msg.attach(MIMEText(text))

    with open(report_path, "rb") as file:
        part = MIMEApplication(file.read(), Name="report.pdf")
        part['Content-Disposition'] = 'attachment; filename=\"report.pdf\"'
        msg.attach(part)

    with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)
