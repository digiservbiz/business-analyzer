"""
Twilio connector for SMS and WhatsApp outreach.
Requires: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER in .env
WhatsApp: TWILIO_FROM_NUMBER should be 'whatsapp:+1234567890'
Gracefully skips if credentials not configured.
"""
import logging
import os

logger = logging.getLogger(__name__)


def _get_client():
    """Return Twilio client or None if not configured."""
    sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    if not sid or not token:
        return None
    try:
        from twilio.rest import Client
        return Client(sid, token)
    except ImportError:
        logger.debug("twilio package not installed — SMS/WhatsApp disabled")
        return None


def send_sms(to_number: str, body: str) -> bool:
    """Send an SMS. Returns True on success."""
    client = _get_client()
    if not client:
        logger.info("SMS skipped (Twilio not configured): %s", to_number[:6] + "***")
        return False
    from_number = os.getenv("TWILIO_FROM_NUMBER", "").strip()
    if not from_number:
        return False
    try:
        msg = client.messages.create(body=body, from_=from_number, to=to_number)
        logger.info("SMS sent to %s: sid=%s", to_number[:6] + "***", msg.sid)
        return True
    except Exception as exc:
        logger.warning("SMS send error: %s", exc)
        return False


def send_whatsapp(to_number: str, body: str) -> bool:
    """
    Send a WhatsApp message. to_number should be in E.164 format (+1234567890).
    Twilio prepends 'whatsapp:' automatically.
    """
    client = _get_client()
    if not client:
        logger.info("WhatsApp skipped (Twilio not configured)")
        return False
    from_number = os.getenv("TWILIO_WHATSAPP_FROM", "").strip()
    if not from_number:
        from_number = os.getenv("TWILIO_FROM_NUMBER", "").strip()
    if not from_number:
        return False
    if not from_number.startswith("whatsapp:"):
        from_number = f"whatsapp:{from_number}"
    to_wa = f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number
    try:
        msg = client.messages.create(body=body, from_=from_number, to=to_wa)
        logger.info("WhatsApp sent: sid=%s", msg.sid)
        return True
    except Exception as exc:
        logger.warning("WhatsApp send error: %s", exc)
        return False


def is_configured() -> bool:
    """Return True if Twilio credentials are present."""
    return bool(
        os.getenv("TWILIO_ACCOUNT_SID", "").strip()
        and os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    )
