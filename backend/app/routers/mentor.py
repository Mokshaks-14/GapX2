from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import get_db
from app.core.security import get_optional_user
from app.services import llm
from app.services.ai_service import AIService

router = APIRouter(prefix="/mentor", tags=["AI Career Mentor"])


def _profile_context(db: Session, user: Optional[models.User]) -> dict:
    if not user:
        return {}
    details = user.profile_details or {}
    roadmap = db.query(models.Roadmap).filter(models.Roadmap.user_id == user.id).order_by(models.Roadmap.created_at.desc()).first()
    interview = db.query(models.MockInterview).filter(models.MockInterview.user_id == user.id, models.MockInterview.overall_score > 0)\
        .order_by(models.MockInterview.created_at.desc()).first()
    solved = db.query(models.CodingSubmission.problem_id).filter(models.CodingSubmission.user_id == user.id,
                                                                 models.CodingSubmission.status == "Accepted").distinct().count()
    return {
        "name": user.full_name, "background": user.role, "education": user.education, "target roles": ", ".join(user.target_roles or []),
        "skills": ", ".join(user.skills or []), "experience level": user.experience_level,
        "college": details.get("college_name"), "current company": details.get("current_company"),
        "project": details.get("project_title"), "roadmap progress": f"{roadmap.progress_percentage}% of {roadmap.target_role}" if roadmap else None,
        "coding problems solved": solved, "last mock interview score": interview.overall_score if interview else None,
        "weak interview areas": "; ".join((interview.feedback or {}).get("weaknesses", [])[:3]) if interview else None,
    }


@router.get("/status")
def mentor_status():
    return {"provider": llm.provider_name()}


@router.post("/chat", response_model=schemas.MentorMessageResponse)
def mentor_chat(req: schemas.MentorMessageRequest, db: Session = Depends(get_db),
                user: Optional[models.User] = Depends(get_optional_user)):
    res = AIService.get_career_advice(req.message, req.history, _profile_context(db, user))
    return schemas.MentorMessageResponse(
        response=res.get("response", "How can I help you today?"),
        suggestions=res.get("suggestions", [])[:3],
        spoken=res.get("spoken"),
    )
