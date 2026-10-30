"""Admin panel API. Separate login (/admin/auth/login) issuing admin-scoped tokens; normal app tokens are rejected."""
import csv
import io
import shutil
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app import models
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_admin_token, get_admin_user, is_admin, verify_password
from app.services import email_verification, llm, tts
from app.services.audit import client_ip, log_event

router = APIRouter(prefix="/admin", tags=["Admin Panel"])

# ─── login with brute-force protection ───
_failed: Dict[str, List[float]] = defaultdict(list)
MAX_FAILS, WINDOW = 5, 15 * 60


class AdminLogin(BaseModel):
    email: str
    password: str


@router.post("/auth/login")
def admin_login(body: AdminLogin, request: Request, db: Session = Depends(get_db)):
    ip = client_ip(request) or "unknown"
    now = time.time()
    _failed[ip] = [t for t in _failed[ip] if now - t < WINDOW]
    if len(_failed[ip]) >= MAX_FAILS:
        log_event("admin", "login_blocked", email=body.email, severity="critical", request=request,
                  details={"reason": "too many failed attempts"})
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in 15 minutes.")

    email = body.email.strip().lower()
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(body.password, user.password_hash) or not is_admin(user) or user.is_active is False:
        _failed[ip].append(now)
        log_event("admin", "login_failed", email=email, severity="warning", request=request,
                  details={"reason": "not an admin" if user and verify_password(body.password, user.password_hash) else "wrong credentials"})
        raise HTTPException(status_code=401, detail="Invalid admin email or password.")
    _failed.pop(ip, None)
    log_event("admin", "login_success", user=user, request=request)
    return {"access_token": create_admin_token(user.id), "token_type": "bearer", "email": user.email, "name": user.full_name}


@router.get("/me")
def admin_me(admin: models.User = Depends(get_admin_user)):
    return {"email": admin.email, "name": admin.full_name}


# ─── overview ───
@router.get("/overview")
def overview(db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    now = datetime.utcnow()
    day, week = now - timedelta(days=1), now - timedelta(days=7)
    interviews = db.query(models.MockInterview).all()
    finished = [i for i in interviews if (i.overall_score or 0) > 0]
    flagged = [i for i in interviews if ((i.behavior_scores or {}).get("integrity") or {}).get("flagged")]
    subs = db.query(models.CodingSubmission)
    total_subs = subs.count()
    accepted = subs.filter(models.CodingSubmission.status == "Accepted").count()
    signups = [(now - timedelta(days=d)).date() for d in range(6, -1, -1)]
    created = [u.created_at.date() for u in db.query(models.User.created_at).filter(models.User.created_at >= now - timedelta(days=7)).all() if u.created_at]
    return {
        "users": db.query(models.User).count(),
        "active_today": db.query(models.User).filter(models.User.last_login_at >= day).count(),
        "new_this_week": db.query(models.User).filter(models.User.created_at >= week).count(),
        "disabled_users": db.query(models.User).filter(models.User.is_active == False).count(),  # noqa: E712
        "interviews": len(interviews),
        "interviews_completed": len(finished),
        "avg_interview_score": round(sum(i.overall_score for i in finished) / len(finished)) if finished else 0,
        "flagged_interviews": len(flagged),
        "submissions": total_subs,
        "acceptance_rate": round(100 * accepted / total_subs) if total_subs else 0,
        "problems": db.query(models.CodingProblem).count(),
        "resumes": db.query(models.Resume).count(),
        "warnings_24h": db.query(models.AuditLog).filter(models.AuditLog.created_at >= day, models.AuditLog.severity != "info").count(),
        "failed_logins_24h": db.query(models.AuditLog).filter(models.AuditLog.created_at >= day, models.AuditLog.event == "login_failed").count(),
        "signups_last_7_days": [{"date": d.strftime("%d %b"), "count": created.count(d)} for d in signups],
    }


# ─── users ───
def _user_row(u: models.User) -> Dict[str, Any]:
    return {"id": u.id, "email": u.email, "name": u.full_name, "role": u.role, "target_role": (u.target_roles or [None])[0],
            "xp": u.xp, "level": u.level, "is_admin": is_admin(u), "is_active": u.is_active is not False,
            "created_at": u.created_at, "last_login_at": u.last_login_at}


@router.get("/users")
def list_users(q: str = "", limit: int = Query(50, le=200), offset: int = 0, db: Session = Depends(get_db),
               admin: models.User = Depends(get_admin_user)):
    query = db.query(models.User)
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(or_(func.lower(models.User.email).like(like), func.lower(models.User.full_name).like(like)))
    total = query.count()
    rows = query.order_by(models.User.created_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "users": [_user_row(u) for u in rows]}


@router.get("/users/{user_id}")
def user_detail(user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    interviews = db.query(models.MockInterview).filter(models.MockInterview.user_id == u.id).order_by(models.MockInterview.created_at.desc()).limit(20).all()
    solved = db.query(models.CodingSubmission.problem_id).filter(models.CodingSubmission.user_id == u.id,
                                                                 models.CodingSubmission.status == "Accepted").distinct().count()
    logs = db.query(models.AuditLog).filter(models.AuditLog.user_id == u.id).order_by(models.AuditLog.created_at.desc()).limit(30).all()
    return {
        **_user_row(u), "profile": u.profile_details or {}, "skills": u.skills or [], "problems_solved": solved,
        "interviews": [{"id": i.id, "role": i.target_role, "type": i.interview_type, "score": i.overall_score, "created_at": i.created_at,
                        "integrity": (i.behavior_scores or {}).get("integrity")} for i in interviews],
        "recent_activity": [_log_row(l) for l in logs],
    }


class StatusChange(BaseModel):
    active: bool
    reason: Optional[str] = None


@router.post("/users/{user_id}/status")
def set_user_status(user_id: int, body: StatusChange, request: Request, db: Session = Depends(get_db),
                    admin: models.User = Depends(get_admin_user)):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if u.id == admin.id:
        raise HTTPException(status_code=400, detail="You can't disable your own admin account.")
    u.is_active = body.active
    db.commit()
    log_event("admin", "user_enabled" if body.active else "user_disabled", user=admin, request=request, severity="warning",
              details={"target_user": u.email, "reason": body.reason or ""})
    return {"ok": True, "is_active": u.is_active}


# ─── interview integrity ───
@router.get("/integrity")
def integrity_reviews(only_flagged: bool = False, db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    rows = db.query(models.MockInterview, models.User).join(models.User, models.User.id == models.MockInterview.user_id)\
        .order_by(models.MockInterview.created_at.desc()).limit(200).all()
    out = []
    for i, u in rows:
        live = (i.behavior_scores or {}).get("integrity_events") or []
        report = (i.behavior_scores or {}).get("integrity") or {}
        if only_flagged and not report.get("flagged"):
            continue
        if not live and not report:
            continue
        out.append({"interview_id": i.id, "user": u.email, "name": u.full_name, "role": i.target_role, "score": i.overall_score,
                    "created_at": i.created_at, "flagged": bool(report.get("flagged")), "summary": report.get("summary"),
                    "counts": report.get("counts") or _count(live), "events": live[-50:]})
    return out


def _count(events: List[Dict[str, Any]]) -> Dict[str, int]:
    c: Dict[str, int] = defaultdict(int)
    for e in events:
        c[e.get("type", "?")] += 1
    return dict(c)


@router.get("/interviews/{interview_id}")
def interview_detail(interview_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    i = db.query(models.MockInterview).filter(models.MockInterview.id == interview_id).first()
    if not i:
        raise HTTPException(status_code=404, detail="Interview not found")
    fb = {k: v for k, v in (i.feedback or {}).items() if k != "engine"}
    return {"id": i.id, "role": i.target_role, "type": i.interview_type, "score": i.overall_score, "created_at": i.created_at,
            "transcript": i.transcript or [], "turns": fb.get("turns", []),
            "integrity": (i.behavior_scores or {}).get("integrity"), "integrity_events": (i.behavior_scores or {}).get("integrity_events", []),
            "body_language": (i.behavior_scores or {}).get("aggregate")}


# ─── audit logs ───
def _log_row(l: models.AuditLog) -> Dict[str, Any]:
    return {"id": l.id, "time": l.created_at, "category": l.category, "event": l.event, "severity": l.severity,
            "user": l.user_email, "ip": l.ip_address, "details": l.details or {}}


def _log_query(db: Session, category: str, severity: str, q: str, days: int):
    query = db.query(models.AuditLog)
    if category:
        query = query.filter(models.AuditLog.category == category)
    if severity:
        query = query.filter(models.AuditLog.severity == severity)
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(or_(func.lower(models.AuditLog.user_email).like(like), func.lower(models.AuditLog.event).like(like)))
    if days:
        query = query.filter(models.AuditLog.created_at >= datetime.utcnow() - timedelta(days=days))
    return query.order_by(models.AuditLog.created_at.desc())


@router.get("/logs")
def logs(category: str = "", severity: str = "", q: str = "", days: int = 7, limit: int = Query(100, le=500), offset: int = 0,
         db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    query = _log_query(db, category, severity, q, days)
    return {"total": query.count(), "logs": [_log_row(l) for l in query.offset(offset).limit(limit).all()]}


@router.get("/logs.csv")
def logs_csv(category: str = "", severity: str = "", q: str = "", days: int = 30, request: Request = None,
             db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["time (UTC)", "category", "event", "severity", "user", "ip", "details"])
    for l in _log_query(db, category, severity, q, days).limit(10000).all():
        writer.writerow([l.created_at, l.category, l.event, l.severity, l.user_email or "", l.ip_address or "", l.details or {}])
    log_event("admin", "logs_exported", user=admin, request=request, details={"category": category, "days": days})
    return Response(content=buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="gapx_audit_logs.csv"'})


# ─── system status ───
@router.get("/system")
def system_status(admin: models.User = Depends(get_admin_user)):
    return {
        "ai_provider": llm.provider_name(),
        "ai_model": settings.GEMINI_MODEL if llm.provider_name() == "gemini" else None,
        "natural_voice": tts.available(), "voice_quota_used_up": tts.quota_exhausted(),
        "email_sending": email_verification.smtp_configured(), "email_verification_required": settings.EMAIL_VERIFICATION_REQUIRED,
        "google_sign_in": bool(settings.GOOGLE_CLIENT_ID),
        "code_runners": {"python": True, "javascript": bool(shutil.which("node")), "java": bool(shutil.which("javac")),
                         "cpp": bool(shutil.which("g++")), "c": bool(shutil.which("gcc")), "judge0_sandbox": bool(settings.JUDGE0_API_KEY)},
        "environment": settings.ENVIRONMENT,
    }


# ─── problems ───
@router.get("/problems")
def problem_stats(db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    out = []
    for p in db.query(models.CodingProblem).order_by(models.CodingProblem.id).all():
        attempts = db.query(models.CodingSubmission).filter(models.CodingSubmission.problem_id == p.id).count()
        ok = db.query(models.CodingSubmission).filter(models.CodingSubmission.problem_id == p.id, models.CodingSubmission.status == "Accepted").count()
        out.append({"id": p.id, "title": p.title, "difficulty": p.difficulty, "category": p.category, "attempts": attempts,
                    "acceptance": round(100 * ok / attempts) if attempts else None, "is_custom": bool(p.is_custom),
                    "tests": len(p.test_cases or [])})
    return out


# ─── adding content: coding problems ───
TYPES = ("int", "double", "bool", "string", "int[]", "string[]", "int[][]")


class TestCaseIn(BaseModel):
    input: str
    output: str = ""
    is_hidden: bool = False


class ProblemIn(BaseModel):
    title: str
    difficulty: str = "Easy"
    category: str
    statement: str
    constraints: str = ""
    explanation: str = ""
    fn: str
    params: List[List[str]]          # [["nums", "int[]"], ["target", "int"]]
    returns: str
    tests: List[TestCaseIn]
    hints: List[str] = []
    company_tags: List[str] = []
    time_complexity: str = "O(N)"
    space_complexity: str = "O(1)"
    unordered: bool = False
    reference_solution: str = ""     # optional Python solution: checks the tests and fills empty outputs
    editorial: str = ""


def _problem_errors(body: ProblemIn) -> List[str]:
    import re as _re
    errs = []
    if len(body.title.strip()) < 3:
        errs.append("Title is too short.")
    if body.difficulty not in ("Easy", "Medium", "Hard"):
        errs.append("Difficulty must be Easy, Medium or Hard.")
    if not _re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", body.fn or ""):
        errs.append("Function name must be a valid identifier, e.g. twoSum.")
    if not body.params:
        errs.append("Add at least one parameter.")
    for p in body.params:
        if len(p) != 2 or not _re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", p[0] or "") or p[1] not in TYPES:
            errs.append(f"Parameter {p} is invalid. Types allowed: {', '.join(TYPES)}.")
    if body.returns not in TYPES:
        errs.append(f"Return type must be one of: {', '.join(TYPES)}.")
    if len(body.tests) < 2:
        errs.append("Add at least 2 test cases.")
    if not any(not t.is_hidden for t in body.tests):
        errs.append("At least one test case must be visible (not hidden), so students see an example.")
    for i, t in enumerate(body.tests, 1):
        lines = t.input.strip("\n").split("\n") if t.input.strip() else []
        if len(lines) != len(body.params):
            errs.append(f"Test {i}: input needs one line per parameter ({len(body.params)} lines), it has {len(lines)}.")
        if not t.output.strip() and not body.reference_solution.strip():
            errs.append(f"Test {i}: expected output is empty. Fill it in, or add a reference solution to compute it.")
    return errs


def _build_problem(body: ProblemIn) -> Dict[str, Any]:
    """Validates the problem, runs the reference solution (if given) and builds the DB fields."""
    from app.services.c_support import c_starter
    from app.services.judge0 import CodeExecutionService
    from app.services.problems_extra import _starters

    errs = _problem_errors(body)
    if errs:
        raise HTTPException(status_code=400, detail=" ".join(errs))
    signature = {"fn": body.fn, "params": body.params, "returns": body.returns, **({"unordered": True} if body.unordered else {})}
    tests = [{"input": t.input.strip("\n"), "output": t.output.strip(), "is_hidden": t.is_hidden} for t in body.tests]

    if body.reference_solution.strip():
        # Run the reference against every test, visible, so we see its real output
        probe = [{**t, "is_hidden": False} for t in tests]
        res = CodeExecutionService.execute_code(body.reference_solution, "python", probe, signature)
        problems = []
        for t, r in zip(tests, res.get("test_results", [])):
            if r["status"] not in ("Accepted", "Wrong Answer"):
                problems.append(f"Test {r['test_case_index'] + 1}: reference solution failed ({r['status']}: {r['actual']}).")
            elif not t["output"]:
                t["output"] = r["actual"]
            elif r["status"] == "Wrong Answer":
                problems.append(f"Test {r['test_case_index'] + 1}: you wrote `{t['output']}` but the reference solution returns `{r['actual']}`.")
        if res.get("status") == "Compilation Error" or (not res.get("test_results") and res.get("status") != "Accepted"):
            problems.append(res.get("message") or "The reference solution could not run.")
        if problems:
            raise HTTPException(status_code=400, detail=" ".join(problems))

    first = next(t for t in tests if not t["is_hidden"])
    editorial = body.editorial.strip()
    if body.reference_solution.strip():
        editorial = (editorial + "\n\n" if editorial else "") + "```python\n" + body.reference_solution.strip() + "\n```"
    fields = {
        "title": body.title.strip(), "difficulty": body.difficulty, "category": body.category.strip() or "General",
        "problem_statement": body.statement.strip(),
        "constraints": "\n".join(f"• {c.strip()}" for c in body.constraints.splitlines() if c.strip()),
        "input_format": "Each line of input is one argument, in order: " + ", ".join(f"`{n}` ({t})" for n, t in body.params) + ".",
        "output_format": f"Return a value of type {body.returns}.",
        "example_input": first["input"], "example_output": first["output"], "explanation": body.explanation.strip(),
        "expected_time_complexity": body.time_complexity or "O(N)", "expected_space_complexity": body.space_complexity or "O(1)",
        "company_tags": [t.strip() for t in body.company_tags if t.strip()] or ["GapX"],
        "hints": [h.strip() for h in body.hints if h.strip()],
        "test_cases": tests, "editorial": editorial or None, "signature": signature, "is_custom": True,
    }
    fields.update(_starters(body.fn, body.params, body.returns))
    fields["starter_code_c"] = c_starter(signature)
    return fields


@router.get("/problems/{problem_id}")
def problem_detail(problem_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    p = db.query(models.CodingProblem).filter(models.CodingProblem.id == problem_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Problem not found")
    return {"id": p.id, "title": p.title, "difficulty": p.difficulty, "category": p.category, "statement": p.problem_statement,
            "constraints": "\n".join(l.lstrip("• ") for l in (p.constraints or "").splitlines()), "explanation": p.explanation or "",
            "signature": p.signature, "tests": p.test_cases or [], "hints": p.hints or [], "company_tags": p.company_tags or [],
            "time_complexity": p.expected_time_complexity, "space_complexity": p.expected_space_complexity,
            "is_custom": bool(p.is_custom), "created_by": p.created_by}


@router.post("/problems")
def create_problem(body: ProblemIn, request: Request, db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    if db.query(models.CodingProblem).filter(func.lower(models.CodingProblem.title) == body.title.strip().lower()).first():
        raise HTTPException(status_code=400, detail="A problem with this title already exists.")
    fields = _build_problem(body)
    p = models.CodingProblem(**fields, created_by=admin.email)
    db.add(p)
    db.commit()
    db.refresh(p)
    log_event("admin", "problem_created", user=admin, request=request, details={"problem": p.title, "id": p.id, "tests": len(p.test_cases)})
    return {"ok": True, "id": p.id, "tests": p.test_cases}


@router.put("/problems/{problem_id}")
def update_problem(problem_id: int, body: ProblemIn, request: Request, db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    p = db.query(models.CodingProblem).filter(models.CodingProblem.id == problem_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Problem not found")
    if not p.is_custom:
        raise HTTPException(status_code=400, detail="Built-in problems can't be edited here. Add a new problem instead.")
    clash = db.query(models.CodingProblem).filter(func.lower(models.CodingProblem.title) == body.title.strip().lower(),
                                                 models.CodingProblem.id != problem_id).first()
    if clash:
        raise HTTPException(status_code=400, detail="Another problem already has this title.")
    for k, v in _build_problem(body).items():
        setattr(p, k, v)
    db.commit()
    log_event("admin", "problem_updated", user=admin, request=request, details={"problem": p.title, "id": p.id})
    return {"ok": True, "id": p.id, "tests": p.test_cases}


@router.delete("/problems/{problem_id}")
def delete_problem(problem_id: int, request: Request, db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    p = db.query(models.CodingProblem).filter(models.CodingProblem.id == problem_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Problem not found")
    if not p.is_custom:
        raise HTTPException(status_code=400, detail="Built-in problems can't be deleted (they come back on restart).")
    title = p.title
    db.delete(p)
    db.commit()
    log_event("admin", "problem_deleted", user=admin, request=request, details={"problem": title, "id": problem_id}, severity="warning")
    return {"ok": True}


# ─── adding content: interview questions ───
class InterviewQuestionIn(BaseModel):
    track: str
    topic: str
    level: str = "Medium"
    question: str
    key_points: List[str]            # one per line: "hash map, dictionary, hashmap" (first word is the label)
    ideal_answer: str
    hint: str = ""


def _iq_row(q: models.InterviewQuestion) -> Dict[str, Any]:
    return {"id": q.id, "track": q.track, "topic": q.topic, "level": q.level, "question": q.question,
            "key_points": [", ".join(g) for g in (q.key_points or [])], "ideal_answer": q.ideal_answer, "hint": q.hint or "",
            "created_by": q.created_by, "created_at": q.created_at}


def _reload_questions(db: Session) -> None:
    from app.services.interview_bank import load_custom_questions
    load_custom_questions(db.query(models.InterviewQuestion).all())


@router.get("/interview-questions")
def list_interview_questions(db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    from app.services.interview_bank import BANK, TRACKS
    return {
        "tracks": [{"id": k, "label": v["label"], "built_in": len([q for q in BANK.get(k, []) if not q.get("custom")])} for k, v in TRACKS.items()],
        "questions": [_iq_row(q) for q in db.query(models.InterviewQuestion).order_by(models.InterviewQuestion.id.desc()).all()],
    }


@router.post("/interview-questions")
def create_interview_question(body: InterviewQuestionIn, request: Request, db: Session = Depends(get_db),
                              admin: models.User = Depends(get_admin_user)):
    from app.services.interview_bank import TRACKS
    errs = []
    if body.track not in TRACKS:
        errs.append("Pick a valid track.")
    if body.level not in ("Easy", "Medium", "Hard"):
        errs.append("Level must be Easy, Medium or Hard.")
    if len(body.question.strip()) < 15:
        errs.append("The question is too short.")
    if len(body.question.split()) > 40:
        errs.append("Keep the question under 40 words so it fits in 2 lines when spoken.")
    groups = [[w.strip() for w in line.split(",") if w.strip()] for line in body.key_points]
    groups = [g for g in groups if g]
    if not groups:
        errs.append("Add at least one key point (what a good answer should mention).")
    if len(body.ideal_answer.strip()) < 20:
        errs.append("Write a model answer of at least one sentence.")
    if errs:
        raise HTTPException(status_code=400, detail=" ".join(errs))
    q = models.InterviewQuestion(track=body.track, topic=body.topic.strip() or "General", level=body.level, question=body.question.strip(),
                                 key_points=groups, ideal_answer=body.ideal_answer.strip(), hint=body.hint.strip() or None, created_by=admin.email)
    db.add(q)
    db.commit()
    db.refresh(q)
    _reload_questions(db)
    log_event("admin", "interview_question_created", user=admin, request=request, details={"track": q.track, "id": q.id, "topic": q.topic})
    return _iq_row(q)


@router.delete("/interview-questions/{question_id}")
def delete_interview_question(question_id: int, request: Request, db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    q = db.query(models.InterviewQuestion).filter(models.InterviewQuestion.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(q)
    db.commit()
    _reload_questions(db)
    log_event("admin", "interview_question_deleted", user=admin, request=request, details={"id": question_id}, severity="warning")
    return {"ok": True}
