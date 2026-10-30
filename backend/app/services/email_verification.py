"""Email ownership check at sign-up: a 6-digit code sent by email.

Codes are stored hashed, expire after 10 minutes, allow 5 attempts, and resends are rate-limited.
Emails are sent over SMTP (e.g. a Gmail account with an App Password). If SMTP isn't configured in
development, the code is printed in the backend console window instead so the flow can still be tested.
"""
import hashlib
import hmac
import logging
import secrets
import smtplib
import ssl
from datetime import datetime, timedelta
from email.message import EmailMessage
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app import models
from app.core.config import settings

logger = logging.getLogger(__name__)

CODE_TTL = timedelta(minutes=10)
RESEND_COOLDOWN = timedelta(seconds=60)
MAX_SENDS_PER_HOUR = 5
MAX_ATTEMPTS = 5


def smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)


def _hash(email: str, code: str) -> str:
    return hmac.new(settings.JWT_SECRET.encode(), f"{email}|{code}".encode(), hashlib.sha256).hexdigest()


def _send_email(to: str, code: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = f"{code} is your GapX AI verification code"
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to
    msg.set_content(
        f"Hi,\n\nYour GapX AI verification code is: {code}\n\n"
        f"It expires in 10 minutes. If you didn't try to create a GapX AI account, you can ignore this email.\n\n— GapX AI"
    )
    msg.add_alternative(f"""
<div style="font-family:Arial,sans-serif;max-width:460px;margin:auto;padding:24px;border:1px solid #e5e7eb;border-radius:16px">
  <h2 style="margin:0 0 8px;color:#4f46e5">GapX AI</h2>
  <p style="color:#374151">Use this code to finish creating your account:</p>
  <div style="font-size:32px;font-weight:800;letter-spacing:8px;color:#111827;margin:16px 0">{code}</div>
  <p style="color:#6b7280;font-size:13px">It expires in 10 minutes. If this wasn't you, ignore this email.</p>
</div>""", subtype="html")
    context = ssl.create_default_context()
    if int(settings.SMTP_PORT) == 465:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, int(settings.SMTP_PORT), context=context, timeout=20) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
    else:
        with smtplib.SMTP(settings.SMTP_HOST, int(settings.SMTP_PORT), timeout=20) as server:
            server.starttls(context=context)
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)


def send_code(db: Session, email: str) -> Tuple[bool, str]:
    """Creates and emails a new code. Returns (ok, message)."""
    now = datetime.utcnow()
    rec = db.query(models.EmailVerification).filter(models.EmailVerification.email == email).first()
    if rec:
        if rec.last_sent_at and now - rec.last_sent_at < RESEND_COOLDOWN:
            wait = int((RESEND_COOLDOWN - (now - rec.last_sent_at)).total_seconds()) + 1
            return False, f"Please wait {wait} seconds before requesting another code."
        if rec.window_start and now - rec.window_start < timedelta(hours=1) and (rec.sends_in_window or 0) >= MAX_SENDS_PER_HOUR:
            return False, "Too many codes requested. Please try again in an hour."
    else:
        rec = models.EmailVerification(email=email)
        db.add(rec)

    code = f"{secrets.randbelow(1_000_000):06d}"
    if not rec.window_start or now - rec.window_start >= timedelta(hours=1):
        rec.window_start, rec.sends_in_window = now, 0
    rec.code_hash = _hash(email, code)
    rec.expires_at = now + CODE_TTL
    rec.attempts = 0
    rec.last_sent_at = now
    rec.sends_in_window = (rec.sends_in_window or 0) + 1

    if smtp_configured():
        try:
            _send_email(email, code)
        except Exception as e:
            db.rollback()
            logger.error("Could not send verification email: %s", e)
            return False, "We couldn't send the email right now. Please check the address and try again."
        db.commit()
        return True, f"We sent a 6-digit code to {email}."
    if settings.is_production:
        db.rollback()
        return False, "Email verification isn't configured on this server."
    db.commit()
    # Development without SMTP: show the code in the backend console window
    print(f"\n{'=' * 60}\n  GapX verification code for {email}: {code}\n  (Email sending isn't set up: add SMTP settings to backend/.env)\n{'=' * 60}\n", flush=True)
    return True, "Email sending isn't set up yet, so the code is shown in the backend window (development mode)."


def check_code(db: Session, email: str, code: str) -> Optional[str]:
    """Returns None if the code is right (and consumes it), otherwise an error message."""
    rec = db.query(models.EmailVerification).filter(models.EmailVerification.email == email).first()
    if not rec or not rec.code_hash:
        return "Please request a verification code first."
    if rec.expires_at and datetime.utcnow() > rec.expires_at:
        return "This code has expired. Please request a new one."
    if (rec.attempts or 0) >= MAX_ATTEMPTS:
        return "Too many wrong attempts. Please request a new code."
    if not hmac.compare_digest(rec.code_hash, _hash(email, (code or "").strip())):
        rec.attempts = (rec.attempts or 0) + 1
        db.commit()
        left = MAX_ATTEMPTS - rec.attempts
        return f"That code isn't right. {left} attempt{'s' if left != 1 else ''} left." if left > 0 else "Too many wrong attempts. Please request a new code."
    rec.code_hash = None  # one-time use
    db.commit()
    return None
