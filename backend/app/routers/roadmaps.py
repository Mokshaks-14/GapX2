import copy
import re
from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app import models, schemas
from app.core.database import get_db
from app.core.security import get_current_user
from app.services import roadmap_service
from app.services.pdf_generator import PDFNotesGenerator
from app.services.gamification import record_activity

router = APIRouter(prefix="/roadmaps", tags=["AI Roadmap Module"])


def _latest(db: Session, user: models.User):
    return db.query(models.Roadmap).filter(models.Roadmap.user_id == user.id)\
        .order_by(models.Roadmap.created_at.desc()).first()


def _respond(roadmap: models.Roadmap, user: models.User) -> schemas.RoadmapResponse:
    """Roadmap plus a live, personalised week-by-week study plan."""
    data = schemas.RoadmapResponse.model_validate(roadmap, from_attributes=True)
    data.study_plan = roadmap_service.study_plan(roadmap.stages_data or [], user.preferred_learning_hours, user.expected_placement_date)
    return data


def _estimate_completion(stages, hours_per_day: int) -> str:
    total_hours = sum(t.get("estimated_hours", 4) for s in stages for t in s.get("topics", []) if not t.get("is_completed"))
    days = max(7, round(total_hours / max(1, hours_per_day or 2)))
    return (datetime.now() + timedelta(days=days)).strftime("%d %B, %Y")


@router.post("/generate", response_model=schemas.RoadmapResponse)
def generate_roadmap(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user.target_roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please select target job roles first.")
    role = current_user.target_roles[0]
    built = roadmap_service.build_roadmap(role, current_user.skills or [])
    stages = roadmap_service.personalise(built["stages"], current_user)

    existing = _latest(db, current_user)
    first_time = existing is None
    if existing:
        roadmap_service.carry_over_progress(existing.stages_data, stages)
        existing.target_role = role
        existing.stages_data = copy.deepcopy(stages)
        existing.progress_percentage = roadmap_service.progress(stages)
        existing.estimated_completion_date = _estimate_completion(stages, current_user.preferred_learning_hours)
        flag_modified(existing, "stages_data")
        roadmap = existing
    else:
        roadmap = models.Roadmap(
            user_id=current_user.id, target_role=role, stages_data=copy.deepcopy(stages),
            progress_percentage=roadmap_service.progress(stages),
            estimated_completion_date=_estimate_completion(stages, current_user.preferred_learning_hours),
        )
        db.add(roadmap)

    if first_time:  # XP only for the first roadmap, so regenerating can't be farmed
        current_user.xp += 100
        current_user.level = max(1, current_user.xp // 500 + 1)
        db.add(models.Notification(
            user_id=current_user.id, title="Roadmap Ready! (+100 XP)", type="Roadmap",
            message=f"Your {len(stages)}-stage {built['track_label']} roadmap is ready, with notes and video links for every topic.",
        ))
    db.commit()
    db.refresh(roadmap)
    return _respond(roadmap, current_user)


@router.get("/current", response_model=schemas.RoadmapResponse)
def get_current_roadmap(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    roadmap = _latest(db, current_user)
    if roadmap and current_user.target_roles and roadmap.target_role != current_user.target_roles[0]:
        return generate_roadmap(db, current_user)
    if not roadmap:
        if current_user.target_roles:
            return generate_roadmap(db, current_user)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No roadmap generated yet. Complete onboarding first.")
    # Upgrade roadmaps created by older versions, keeping completed topics
    if not roadmap_service.is_current_format(roadmap.stages_data or []):
        built = roadmap_service.build_roadmap(roadmap.target_role, current_user.skills or [])
        built["stages"] = roadmap_service.personalise(built["stages"], current_user)
        roadmap_service.carry_over_progress(roadmap.stages_data, built["stages"])
        roadmap.stages_data = built["stages"]
        roadmap.progress_percentage = roadmap_service.progress(built["stages"])
        flag_modified(roadmap, "stages_data")
        db.commit()
        db.refresh(roadmap)
    return _respond(roadmap, current_user)


@router.post("/toggle-topic", response_model=schemas.RoadmapResponse)
def toggle_topic(request: schemas.ToggleTopicRequest, db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    roadmap = _latest(db, current_user)
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")

    stages = copy.deepcopy(roadmap.stages_data)
    target = None
    for stage in stages:
        for topic in stage.get("topics", []):
            if str(topic.get("id")) == str(request.topic_id) and (target is None or str(stage.get("id")) == str(request.stage_id)):
                target = topic
    if target is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    new_state = bool(request.is_completed)
    if bool(target.get("is_completed")) != new_state:  # only award/remove XP on a real change
        target["is_completed"] = new_state
        if new_state:
            record_activity(current_user)
            current_user.xp += 50
            new_level = current_user.xp // 500 + 1
            if new_level > current_user.level:
                current_user.level = new_level
                db.add(models.Notification(user_id=current_user.id, title=f"Level Up! Level {new_level}", type="Achievement",
                                           message=f"You reached Level {new_level} with {current_user.xp} XP. Keep going!"))
        else:
            current_user.xp = max(0, current_user.xp - 50)
            current_user.level = max(1, current_user.xp // 500 + 1)

    roadmap.stages_data = stages
    roadmap.progress_percentage = roadmap_service.progress(stages)
    flag_modified(roadmap, "stages_data")
    db.commit()
    db.refresh(roadmap)
    return _respond(roadmap, current_user)


def _find_topic(roadmap, stage_id: str, topic_id: str):
    stage_title, topic_title = f"Stage {stage_id}", f"Topic {topic_id}"
    for s in (roadmap.stages_data if roadmap else []) or []:
        for t in s.get("topics", []):
            if str(t.get("id")) == str(topic_id):
                topic_title, stage_title = t.get("title", topic_title), s.get("title", stage_title)
                if str(s.get("id")) == str(stage_id):
                    return stage_title, topic_title
    return stage_title, topic_title


@router.get("/notes/{stage_id}/{topic_id}")
def get_topic_notes(stage_id: str, topic_id: str, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)) -> Dict[str, Any]:
    roadmap = _latest(db, current_user)
    stage_title, topic_title = _find_topic(roadmap, stage_id, topic_id)
    role = roadmap.target_role if roadmap else (current_user.target_roles or ["Software Engineer"])[0]
    return roadmap_service.topic_notes(topic_title, stage_title, role)


def _pdf_response(buffer, filename: str) -> Response:
    return Response(content=buffer.getvalue(), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/notes-pdf/{stage_id}/{topic_id}")
def download_topic_notes(stage_id: str, topic_id: str, db: Session = Depends(get_db),
                         current_user: models.User = Depends(get_current_user)):
    roadmap = _latest(db, current_user)
    stage_title, topic_title = _find_topic(roadmap, stage_id, topic_id)
    role = roadmap.target_role if roadmap else (current_user.target_roles or ["Software Engineer"])[0]
    notes = roadmap_service.topic_notes(topic_title, stage_title, role)
    clean = re.sub(r"[^A-Za-z0-9]+", "_", topic_title).strip("_")
    return _pdf_response(PDFNotesGenerator.generate_notes_pdf(notes), f"GapX_Notes_{clean}.pdf")


@router.get("/cheatsheet-pdf")
def download_roadmap_cheatsheet(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """All last-minute notes for the user's roadmap in one PDF."""
    roadmap = _latest(db, current_user)
    if not roadmap:
        raise HTTPException(status_code=404, detail="Generate a roadmap first.")
    notes = roadmap_service.all_notes(roadmap.stages_data or [], roadmap.target_role)
    if not notes:
        raise HTTPException(status_code=409, detail="Regenerate your roadmap to get downloadable notes.")
    buffer = PDFNotesGenerator.generate_cheatsheet_pdf(roadmap.target_role, notes)
    clean = re.sub(r"[^A-Za-z0-9]+", "_", roadmap.target_role).strip("_")
    return _pdf_response(buffer, f"GapX_{clean}_Last_Minute_Notes.pdf")
