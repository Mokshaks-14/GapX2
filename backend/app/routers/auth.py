import logging
import secrets

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.core import security
from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}
DEMO_EMAIL = "demo@gapx.ai"


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


def demo_login_enabled() -> bool:
    return settings.ALLOW_DEMO_LOGIN and not settings.is_production


@router.get("/config")
def auth_config():
    """Tells the frontend which sign-in options are available."""
    return {
        "google_client_id": settings.GOOGLE_CLIENT_ID or None,
        "demo_login_enabled": demo_login_enabled(),
    }


@router.post("/register", response_model=schemas.Token)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    email = user_in.email.strip().lower()
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A user with this email already exists.")

    user = models.User(
        email=email,
        password_hash=security.get_password_hash(user_in.password),
        full_name=user_in.full_name or email.split("@")[0],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _sync_admin_flag(user, db)
    return _token_response(user)


@router.post("/login", response_model=schemas.Token)
def login(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    email = user_in.email.strip().lower()
    # Older accounts may have been stored with mixed-case emails
    user = db.query(models.User).filter(models.User.email == email).first() or \
        db.query(models.User).filter(models.User.email == user_in.email.strip()).first()
    if not user or not security.verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password.")
    _sync_admin_flag(user, db)
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
def google_login(payload: schemas.GoogleLoginRequest, db: Session = Depends(get_db)):
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
    _sync_admin_flag(user, db)
    return _token_response(user)


@router.post("/demo", response_model=schemas.Token)
def demo_login(db: Session = Depends(get_db)):
    """One-click demo account for local development. Disabled in production."""
    if not demo_login_enabled():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Demo login is disabled.")
    user = db.query(models.User).filter(models.User.email == DEMO_EMAIL).first()
    if not user:
        user = models.User(
            email=DEMO_EMAIL,
            password_hash=security.get_password_hash(secrets.token_urlsafe(32)),
            full_name="Demo Student",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return _token_response(user)
