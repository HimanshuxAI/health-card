import os
import smtplib
from email.mime.text import MIMEText

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
FROM_EMAIL = os.getenv("SOS_FROM_EMAIL", "")


def send_alert_email(to: str, subject: str, body: str) -> str:
    """Send one email. Returns a status token: SENT | SKIPPED | FAILED.

    Never raises — a mail outage must never block an emergency alert.
    """
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and FROM_EMAIL):
        return "SKIPPED"
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = FROM_EMAIL
        msg["To"] = to
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=8) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return "SENT"
    except Exception:
        return "FAILED"
