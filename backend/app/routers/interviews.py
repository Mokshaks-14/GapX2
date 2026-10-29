from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app import models, schemas
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.behavior_analyzer import BehaviorAnalyzer
from app.services.interview_bank import TRACKS
from app.services.interview_engine import InterviewEngine
from app.services.gamification import record_activity

router = APIRouter(prefix="/interviews", tags=["AI Mock Interviews"])

MAX_XP_INTERVIEWS_PER_DAY = 2


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
    return schemas.InterviewStartResponse(
        interview_id=interview.id, first_question=started["question"], speech_text=started["question"],
        difficulty=started["difficulty"], phase=started["phase"], track=state["track"],
        track_label=state["track_label"], total_questions=started["total_questions"],
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
        interview.behavior_scores = {"telemetry_log": telemetry, "aggregate": behavior}
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
    else:
        store["engine"] = state
        interview.feedback = store
        interview.behavior_scores = {"telemetry_log": telemetry}

    for field in ("transcript", "feedback", "behavior_scores"):
        flag_modified(interview, field)
    db.commit()

    return schemas.InterviewMessageResponse(**{k: v for k, v in result.items() if k in schemas.InterviewMessageResponse.model_fields})


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
