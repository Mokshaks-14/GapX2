import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import models
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.migrations import upgrade_schema
from app.routers import admin, auth, coding, interviews, mentor, resumes, roadmaps, tts, users
from app.services.problem_bank import ALL_PROBLEMS as PROBLEMS_DATA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create missing tables and add missing columns (never drops data)
upgrade_schema(engine)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

for router in (auth, users, resumes, roadmaps, coding, interviews, mentor, admin, tts):
    app.include_router(router.router, prefix=settings.API_V1_STR)

PROBLEM_FIELDS = [
    "difficulty", "category", "company_tags", "problem_statement", "constraints", "input_format",
    "output_format", "example_input", "example_output", "explanation", "expected_time_complexity",
    "expected_space_complexity", "starter_code_python", "starter_code_java", "starter_code_cpp",
    "starter_code_js", "starter_code_c", "hints", "test_cases", "editorial", "signature",
]


def seed_problems(db: Session) -> None:
    """Inserts new problems from the problem bank and refreshes existing ones (matched by title)."""
    existing = {p.title: p for p in db.query(models.CodingProblem).all()}
    added = 0
    for data in PROBLEMS_DATA:
        problem = existing.get(data["title"])
        if problem is None:
            problem = models.CodingProblem(title=data["title"])
            db.add(problem)
            added += 1
        for field in PROBLEM_FIELDS:
            if field in data:
                setattr(problem, field, data[field])
    db.commit()
    logger.info("Problem bank synchronized: %d problems (%d new).", len(PROBLEMS_DATA), added)


def ensure_admin_account(db: Session) -> None:
    """Creates (or updates) the admin-panel account from ADMIN_EMAIL / ADMIN_PASSWORD in backend/.env."""
    from app.core.security import get_password_hash, verify_password
    email = (settings.ADMIN_EMAIL or "").strip().lower()
    if not email or not settings.ADMIN_PASSWORD:
        return
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        user = models.User(email=email, full_name="GapX Admin", password_hash=get_password_hash(settings.ADMIN_PASSWORD), role="Admin")
        db.add(user)
    elif not verify_password(settings.ADMIN_PASSWORD, user.password_hash):
        user.password_hash = get_password_hash(settings.ADMIN_PASSWORD)
    user.is_admin = True
    user.is_active = True
    db.commit()
    logger.info("Admin panel account ready: %s", email)


@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        seed_problems(db)
        ensure_admin_account(db)
        from app.services.interview_bank import load_custom_questions
        n = load_custom_questions(db.query(models.InterviewQuestion).all())
        if n:
            logger.info("Loaded %d interview questions added from the admin panel.", n)
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Welcome to GapX AI Placement Preparation API. Check /docs for swagger specs!"}
