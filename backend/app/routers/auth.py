import logging
import secrets

import requests
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.services import email_verification
from app.services.audit import log_event
from app.services.email_check import validate_signup_email
from app.services.validation import name_problem, password_problem

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


def _sync_admin_flag(user: models.User, db: Session) -> None:
    """Grants admin rights to emails listed in ADMIN_EMAILS (and never by email prefix)."""
    if user.email.lower() in settings.admin_emails and not user.is_admin:
        user.is_admin = True
        db.commit()


def _token_response(user: models.User) -> dict:
    return {
        "access_token": security.create_access_token(user.id),
        "token_type": "bearer",
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
    }


@router.get("/config")
def auth_config():
    """Tells the frontend which sign-in options are available."""
    return {
        "google_client_id": settings.GOOGLE_CLIENT_ID or None,
        "email_verification": settings.EMAIL_VERIFICATION_REQUIRED,
    }


@router.post("/check-email")
def check_email(payload: schemas.EmailCheckRequest, db: Session = Depends(get_db)):
    """Tells the sign-in screen whether to ask for a password (existing user) or show registration."""
    email = payload.email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    exists = db.query(models.User).filter(models.User.email == email).first() is not None or         db.query(models.User).filter(models.User.email == payload.email.strip()).first() is not None
    if not exists and settings.EMAIL_DOMAIN_CHECK:
        problem = validate_signup_email(email)
        if problem:
            log_event("auth", "signup_email_rejected", email=email, severity="warning", details={"reason": problem})
            raise HTTPException(status_code=400, detail=problem)
    return {"exists": exists}


@router.post("/send-code")
def send_verification_code(payload: schemas.EmailCheckRequest, db: Session = Depends(get_db)):
    """Emails a 6-digit code that proves the person owns the address (needed to register)."""
    email = payload.email.strip().lower()
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=400, detail="An account with this email already exists. Please sign in.")
    if settings.EMAIL_DOMAIN_CHECK:
        problem = validate_signup_email(email)
        if problem:
            raise HTTPException(status_code=400, detail=problem)
    ok, message = email_verification.send_code(db, email)
    if not ok:
        raise HTTPException(status_code=429 if "wait" in message or "Too many" in message else 400, detail=message)
    return {"sent": True, "message": message, "dev_mode": not email_verification.smtp_configured()}


@router.post("/register", response_model=schemas.Token)
def register(user_in: schemas.UserCreate, request: Request, db: Session = Depends(get_db)):
    email = user_in.email.strip().lower()
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A user with this email already exists.")
    if settings.EMAIL_DOMAIN_CHECK:
        problem = validate_signup_email(email)
        if problem:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=problem)
    problem = name_problem(user_in.full_name or "") or password_problem(user_in.password, email, user_in.full_name or "")
    if problem:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=problem)
    if settings.EMAIL_VERIFICATION_REQUIRED:
        problem = email_verification.check_code(db, email, user_in.verification_code or "")
        if problem:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=problem)

    user = models.User(
        email=email,
        password_hash=security.get_password_hash(user_in.password),
        full_name=user_in.full_name or email.split("@")[0],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _sync_admin_flag(user, db)
    log_event("auth", "signup", user=user, request=request, details={"method": "email + verification code" if settings.EMAIL_VERIFICATION_REQUIRED else "email"})
    return _token_response(user)


@router.post("/login", response_model=schemas.Token)
def login(user_in: schemas.UserLogin, request: Request, db: Session = Depends(get_db)):
    email = user_in.email.strip().lower()
    # Older accounts may have been stored with mixed-case emails
    user = db.query(models.User).filter(models.User.email == email).first() or \
        db.query(models.User).filter(models.User.email == user_in.email.strip()).first()
    if not user or not security.verify_password(user_in.password, user.password_hash):
        log_event("auth", "login_failed", email=email, severity="warning", request=request,
                  details={"reason": "unknown email" if not user else "wrong password"})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password.")
    if user.is_active is False:
        log_event("auth", "login_blocked", user=user, severity="warning", request=request, details={"reason": "account disabled"})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been disabled. Please contact support.")
    _sync_admin_flag(user, db)
    user.last_login_at = datetime.utcnow()
    db.commit()
    log_event("auth", "login", user=user, request=request)
    return _token_response(user)


def _verify_google_credential(credential: str) -> dict:
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED,
                            detail="Google sign-in is not configured on this server.")
    try:
        resp = requests.get(GOOGLE_TOKENINFO_URL, params={"id_token": credential}, timeout=8)
    except requests.RequestException:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not reach Google to verify sign-in.")
    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google credential.")

    info = resp.json()
    if info.get("aud") != settings.GOOGLE_CLIENT_ID or info.get("iss") not in GOOGLE_ISSUERS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google credential was issued for a different app.")
    if str(info.get("email_verified")).lower() != "true" or not info.get("email"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google account email is not verified.")
    return info


@router.post("/google", response_model=schemas.Token)
def google_login(payload: schemas.GoogleLoginRequest, request: Request, db: Session = Depends(get_db)):
    """Signs in with a Google ID token produced by Google Identity Services on the frontend."""
    info = _verify_google_credential(payload.credential)
    email = info["email"].lower()

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(
            email=email,
            # Random unusable password: this account signs in through Google only
            password_hash=security.get_password_hash(secrets.token_urlsafe(32)),
            full_name=info.get("name") or email.split("@")[0],
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    if user.is_active is False:
        log_event("auth", "login_blocked", user=user, severity="warning", request=request, details={"reason": "account disabled", "method": "google"})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been disabled. Please contact support.")
    _sync_admin_flag(user, db)
    user.last_login_at = datetime.utcnow()
    db.commit()
    log_event("auth", "login", user=user, request=request, details={"method": "google"})
    return _token_response(user)
