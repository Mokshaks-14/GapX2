from datetime import datetime, timedelta
from typing import Any, Optional, Union

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app import models
from app.core.config import settings
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return jwt.encode({"exp": expire, "sub": str(subject)}, settings.JWT_SECRET, algorithm=settings.ALGORITHM)


def _credentials_exception(detail: str = "Could not validate credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def user_from_token(db: Session, token: Optional[str]) -> Optional[models.User]:
    """Returns the user a valid, unexpired token belongs to, or None."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        return None
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_current_user(db: Session = Depends(get_db), token: Optional[str] = Depends(oauth2_scheme)) -> models.User:
    if not token:
        raise _credentials_exception("Not authenticated")
    user = user_from_token(db, token)
    if user is None:
        raise _credentials_exception("Session expired or invalid. Please sign in again.")
    return user


def get_optional_user(db: Session = Depends(get_db), token: Optional[str] = Depends(oauth2_scheme)) -> Optional[models.User]:
    """For endpoints that work for guests too (e.g. the AI mentor)."""
    return user_from_token(db, token)


def is_admin(user: models.User) -> bool:
    return bool(user.is_admin) or user.email.lower() in settings.admin_emails


def get_admin_user(user: models.User = Depends(get_current_user)) -> models.User:
    if not is_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator privileges required.")
    return user
