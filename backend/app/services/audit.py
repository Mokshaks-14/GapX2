"""Audit log: every important event is written to the database and to the backend console.

Categories: auth, interview, integrity, coding, resume, admin.
Severity:   info, warning, critical.
Events are written with their own database session, so they're kept even if the request later fails.
"""
import logging
from typing import Any, Dict, Optional

from fastapi import Request

from app.core.database import SessionLocal

logger = logging.getLogger("gapx.audit")


def client_ip(request: Optional[Request]) -> Optional[str]:
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def log_event(category: str, event: str, *, user: Any = None, email: Optional[str] = None,
              details: Optional[Dict[str, Any]] = None, severity: str = "info", request: Optional[Request] = None) -> None:
    from app import models  # local import avoids a circular import at startup

    user_id = getattr(user, "id", None)
    user_email = email or getattr(user, "email", None)
    ip = client_ip(request)
    line = f"[{severity.upper()}] {category}.{event} user={user_email or '-'} ip={ip or '-'} {details or ''}"
    (logger.warning if severity in ("warning", "critical") else logger.info)(line)
    db = SessionLocal()
    try:
        db.add(models.AuditLog(category=category, event=event, severity=severity, user_id=user_id,
                               user_email=user_email, ip_address=ip, details=details or {}))
        db.commit()
    except Exception as e:  # logging must never break the app
        db.rollback()
        logger.error("Could not write audit log: %s", e)
    finally:
        db.close()
