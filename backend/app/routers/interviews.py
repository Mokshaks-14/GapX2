from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app import models, schemas
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.behavior_analyzer import BehaviorAnalyzer
from app.services.interview_bank import TRACKS
from app.services import tts
from app.services.audit import log_event
from app.services.interview_engine import InterviewEngine
from app.services.gamification import record_activity

router = APIRouter(prefix="/interviews", tags=["AI Mock Interviews"])

MAX_XP_INTERVIEWS_PER_DAY = 2


def _candidate_profile(db: Session, user: models.User) -> dict:
    """Profile details that personalise the interview (from onboarding and the latest resume)."""
    details = user.profile_details or {}
    profile = {
        "skills": list(dict.fromkeys((user.skills or []) + (user.languages_known or []))),
        "college": details.get("college_name"),
        "company": details.get("current_company"),
        "project_title": details.get("project_title"),
        "project_stack": details.get("project_stack"),
        "project_description": details.get("project_description"),
    }
    if not profile["project_title"]:
        resume = db.query(models.Resume).filter(models.Resume.user_id == user.id).order_by(models.Resume.created_at.desc()).first()
        projects = ((resume.resume_data or {}).get("projects") or []) if resume else []
        first = next((p for p in projects if isinstance(p, dict) and (p.get("name") or p.get("title"))), None)
        if first:
            profile["project_title"] = first.get("name") or first.get("title")
            profile["project_stack"] = first.get("stack") or first.get("technologies")
    return profile


@router.get("/tracks")
def list_tracks():
    """Fields the candidate can be interviewed for."""
    return [{"id": k, "label": v["label"]} for k, v in TRACKS.items()]


@router.post("/start", response_model=schemas.InterviewStartResponse)
def start_interview(req: schemas.InterviewStartRequest, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    started = InterviewEngine.start(
        role=req.target_role,
        interview_type=req.interview_type,
        experience_level=req.experience_level,
        track_hint=req.track or req.topic_domain,
        job_description=(req.job_description or "").strip(),
        candidate_name=current_user.full_name,
        length=req.num_questions or 8,
        profile=_candidate_profile(db, current_user),
    )
    state = started["state"]
    interview = models.MockInterview(
        user_id=current_user.id,
        target_role=state["role"],
        experience_level=req.experience_level or "Fresher",
        interview_type=req.interview_type or "Mixed",
        transcript=[{"role": "interviewer", "text": started["question"]}],
        feedback={"engine": state, "job_description": state["job_description"]},
        behavior_scores={"telemetry_log": []},
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    log_event("interview", "started", user=current_user, details={"interview_id": interview.id, "role": state["role"], "type": interview.interview_type})
    for part in started["speech_parts"]:
        tts.warm(part)
    return schemas.InterviewStartResponse(
        interview_id=interview.id, first_question=started["question"], speech_text=started["question"],
        difficulty=started["difficulty"], phase=started["phase"], track=state["track"],
        track_label=state["track_label"], total_questions=started["total_questions"], speech_parts=started["speech_parts"],
    )


def _award_xp(db: Session, user: models.User, interview: models.MockInterview, answered: int) -> int:
    """XP scales with the score; only completed sessions count, capped per day to prevent farming."""
    if answered < 3:
        return 0
    since = datetime.utcnow() - timedelta(days=1)
    recent = db.query(models.MockInterview).filter(
        models.MockInterview.user_id == user.id,
        models.MockInterview.created_at >= since,
        models.MockInterview.id != interview.id,
    ).all()
    awarded_today = sum(1 for i in recent if (i.feedback or {}).get("xp_awarded"))
    if awarded_today >= MAX_XP_INTERVIEWS_PER_DAY:
        return 0
    xp = 100 + 2 * (interview.overall_score or 0)
    record_activity(user)
    user.xp += xp
    user.level = max(user.level, user.xp // 500 + 1)
    return xp


@router.post("/{interview_id}/answer", response_model=schemas.InterviewMessageResponse)
def submit_interview_answer(interview_id: int, req: schemas.InterviewMessageRequest, db: Session = Depends(get_db),
                            current_user: models.User = Depends(get_current_user)):
    interview = db.query(models.MockInterview).filter(
        models.MockInterview.id == interview_id, models.MockInterview.user_id == current_user.id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview session not found")

    store = dict(interview.feedback or {})
    state = store.get("engine")
    if not state:
        raise HTTPException(status_code=409, detail="This interview was created by an older version. Please start a new one.")
    if state.get("finished"):
        raise HTTPException(status_code=409, detail="This interview has already finished.")

    frame = BehaviorAnalyzer.analyze_frame_telemetry(req.attention_metric, req.smile_metric, req.stress_metric, req.eye_contact_metric)
    telemetry = list((interview.behavior_scores or {}).get("telemetry_log", []))
    frame["wpm"] = req.wpm_metric
    frame["filler_words"] = req.filler_words_count
    frame["integrity_events"] = [e for e in (req.integrity_events or []) if e in ("multiple_faces", "background_motion", "face_missing", "phone_detected", "tab_switch", "fullscreen_exit", "paste_attempt")][:20]
    telemetry.append(frame)

    result = InterviewEngine.answer(state, req.answer, {"wpm": req.wpm_metric, "face": frame if frame.get("has_face_data") else None})

    transcript = list(interview.transcript or [])
    if not result.get("is_repeat"):
        transcript.append({"role": "candidate", "text": req.answer})
    transcript.append({"role": "interviewer", "text": result["speech_text_to_speak"]})
    interview.transcript = transcript

    if result["is_finished"]:
        behavior = BehaviorAnalyzer.get_aggregate_behavior_report(telemetry)
        report = InterviewEngine.report(state, behavior)
        for key in ("technical_score", "communication_score", "confidence_score", "problem_solving_score", "leadership_score", "overall_score"):
            setattr(interview, key, report[key])
        answered = len([t for t in state["turns"] if t.get("score") is not None])
        final = dict(report["feedback"])
        final.update({"engine": state, "job_description": state.get("job_description", "")})
        interview.feedback = final
        from app.services.behavior_analyzer import integrity_report
        live_events = list((interview.behavior_scores or {}).get("integrity_events", []))
        integ = integrity_report(telemetry, live_events)
        interview.behavior_scores = {"telemetry_log": telemetry, "aggregate": behavior, "integrity": integ, "integrity_events": live_events}
        xp = _award_xp(db, current_user, interview, answered)
        final["xp_awarded"] = xp
        interview.feedback = final
        db.add(models.Notification(
            user_id=current_user.id,
            title=f"Mock Interview Completed{f' (+{xp} XP)' if xp else ''}",
            message=f"{interview.interview_type} interview for '{interview.target_role}'. Overall score: {interview.overall_score}/100.",
            type="Interview",
        ))
        result["current_live_score"] = interview.overall_score
        log_event("interview", "completed", user=current_user, severity="warning" if integ["flagged"] else "info",
                  details={"interview_id": interview.id, "score": interview.overall_score, "integrity_flagged": integ["flagged"],
                           "integrity": integ["counts"]})
    else:
        store["engine"] = state
        interview.feedback = store
        interview.behavior_scores = {"telemetry_log": telemetry,
                                     "integrity_events": list((interview.behavior_scores or {}).get("integrity_events", []))}

    for field in ("transcript", "feedback", "behavior_scores"):
        flag_modified(interview, field)
    db.commit()

    # Start generating the interviewer's voice now, so it's (nearly) ready when the browser asks for it
    for part in (result.get("speech_parts") or [result.get("speech_text_to_speak")]):
        if part:
            tts.warm(part)
    return schemas.InterviewMessageResponse(**{k: v for k, v in result.items() if k in schemas.InterviewMessageResponse.model_fields})


INTEGRITY_TYPES = ("multiple_faces", "background_motion", "face_missing", "phone_detected", "tab_switch", "fullscreen_exit", "paste_attempt")


class IntegrityEvent(BaseModel):
    type: str
    question_number: Optional[int] = None


@router.post("/{interview_id}/integrity")
def report_integrity_event(interview_id: int, body: IntegrityEvent, request: Request, db: Session = Depends(get_db),
                           current_user: models.User = Depends(get_current_user)):
    """Called by the browser the moment a proctoring warning happens (logged and stored immediately)."""
    if body.type not in INTEGRITY_TYPES:
        raise HTTPException(status_code=400, detail="Unknown integrity event")
    interview = db.query(models.MockInterview).filter(
        models.MockInterview.id == interview_id, models.MockInterview.user_id == current_user.id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview session not found")
    scores = dict(interview.behavior_scores or {})
    events = list(scores.get("integrity_events", []))
    if len(events) < 300:
        events.append({"type": body.type, "question": body.question_number, "at": datetime.utcnow().isoformat(timespec="seconds")})
    scores["integrity_events"] = events
    interview.behavior_scores = scores
    flag_modified(interview, "behavior_scores")
    db.commit()
    log_event("integrity", body.type, user=current_user, request=request,
              severity="critical" if body.type in ("phone_detected", "multiple_faces") else "warning",
              details={"interview_id": interview_id, "question": body.question_number})
    return {"ok": True}


def _serialize(interview: models.MockInterview) -> dict:
    feedback = {k: v for k, v in (interview.feedback or {}).items() if k != "engine"}
    return {
        "id": interview.id, "target_role": interview.target_role, "interview_type": interview.interview_type,
        "technical_score": interview.technical_score or 0, "communication_score": interview.communication_score or 0,
        "confidence_score": interview.confidence_score or 0, "problem_solving_score": interview.problem_solving_score or 0,
        "leadership_score": interview.leadership_score or 0, "overall_score": interview.overall_score or 0,
        "feedback": feedback, "behavior_scores": {k: v for k, v in (interview.behavior_scores or {}).items() if k != "telemetry_log"},
        "created_at": interview.created_at,
    }


@router.get("/{interview_id}/feedback", response_model=schemas.InterviewFeedbackResponse)
def get_interview_feedback(interview_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    interview = db.query(models.MockInterview).filter(
        models.MockInterview.id == interview_id, models.MockInterview.user_id == current_user.id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview session not found")
    if not (interview.feedback or {}).get("engine", {}).get("finished", True):
        raise HTTPException(status_code=400, detail="Interview is still in progress.")
    return _serialize(interview)


@router.get("/latest", response_model=schemas.InterviewFeedbackResponse)
def get_latest_interview(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    interviews = db.query(models.MockInterview).filter(models.MockInterview.user_id == current_user.id)\
        .order_by(models.MockInterview.created_at.desc()).limit(10).all()
    for interview in interviews:
        engine = (interview.feedback or {}).get("engine")
        if engine is None or engine.get("finished"):
            if interview.overall_score:
                return _serialize(interview)
    raise HTTPException(status_code=404, detail="No completed mock interview found yet")
