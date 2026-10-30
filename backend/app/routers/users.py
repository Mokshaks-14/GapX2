from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas
from app.core.database import get_db
from app.core.security import get_current_user, is_admin

router = APIRouter(prefix="/users", tags=["Users & Onboarding"])

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    response = schemas.UserResponse.model_validate(current_user)
    response.is_admin = is_admin(current_user)
    return response

@router.get("/readiness")
def get_placement_readiness(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Fetch latest roadmap progress
    roadmap = db.query(models.Roadmap)\
        .filter(models.Roadmap.user_id == current_user.id)\
        .order_by(models.Roadmap.created_at.desc())\
        .first()
    roadmap_pct = roadmap.progress_percentage if roadmap else 0.0

    # 2. Fetch coding progress
    total_probs = db.query(models.CodingProblem).count()
    solved_submissions = db.query(models.CodingSubmission)\
        .filter(models.CodingSubmission.user_id == current_user.id, models.CodingSubmission.status == "Accepted")\
        .all()
    solved_ids = {s.problem_id for s in solved_submissions}
    solved_count = len(solved_ids)
    coding_pct = round((solved_count / max(1, total_probs)) * 100, 1)

    # 3. Fetch latest resume ATS score
    resume = db.query(models.Resume)\
        .filter(models.Resume.user_id == current_user.id)\
        .order_by(models.Resume.created_at.desc())\
        .first()
    ats_score = resume.ats_score if resume else 50

    # 4. Fetch latest interview overall score
    interview = db.query(models.MockInterview)\
        .filter(models.MockInterview.user_id == current_user.id)\
        .order_by(models.MockInterview.created_at.desc())\
        .first()
    interview_score = interview.overall_score if interview else 60

    # Dynamic composite formula
    composite_score = int(
        (0.25 * roadmap_pct) +
        (0.25 * coding_pct) +
        (0.25 * ats_score) +
        (0.25 * interview_score)
    )
    # Ensure minimum base score for onboarded users
    final_readiness = min(max(composite_score, 35 if current_user.education else 10), 100)

    # Determine status level
    if final_readiness >= 80:
        readiness_status = "Tier-1 Placement Ready"
    elif final_readiness >= 60:
        readiness_status = "Intermediate Candidate"
    else:
        readiness_status = "Foundation Building Needed"

    # Dynamic target company matches based on score
    companies = [
        {"name": "Google", "match": f"{min(98, final_readiness + 5)}%", "role": current_user.target_roles[0] if current_user.target_roles else "Software Engineer"},
        {"name": "Microsoft", "match": f"{min(96, final_readiness + 3)}%", "role": "SDE-1"},
        {"name": "Amazon", "match": f"{min(95, final_readiness + 2)}%", "role": "SDE-1"},
        {"name": "Atlassian", "match": f"{min(94, final_readiness)}%", "role": "Graduate Engineer"},
    ]

    return {
        "placement_readiness_score": final_readiness,
        "readiness_status": readiness_status,
        "roadmap_progress": roadmap_pct,
        "coding_progress": coding_pct,
        "questions_solved": solved_count,
        "total_questions": total_probs,
        "ats_score": ats_score,
        "mock_interview_score": interview_score,
        "xp": current_user.xp,
        "level": current_user.level,
        "streak": current_user.streak,
        "matched_companies": companies,
        "weak_areas": resume.weaknesses if resume and resume.weaknesses else ["System Design Deep Dive", "Graph Algorithms"],
        "strengths": resume.strengths if resume and resume.strengths else ["Core Language Fundamentals", "Problem Solving"]
    }

@router.put("/onboard", response_model=schemas.UserResponse)
@router.post("/onboard", response_model=schemas.UserResponse)
def onboard_user(
    onboard_data: schemas.UserOnboard,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    from sqlalchemy.orm.attributes import flag_modified
    from app.services.validation import onboarding_problems
    problems = onboarding_problems(onboard_data.model_dump())
    if problems:
        raise HTTPException(status_code=400, detail=" ".join(problems))
    
    current_user.role = onboard_data.role
    
    # Dynamic profile formatting based on role
    edu = onboard_data.education
    sem = onboard_data.semester
    
    if not edu or edu.strip() == "":
        if onboard_data.role == "Student":
            deg = onboard_data.degree_branch or "B.Tech Computer Science"
            college = f" ({onboard_data.college_name})" if onboard_data.college_name else ""
            grad = f" - Class of {onboard_data.graduation_year}" if onboard_data.graduation_year else ""
            edu = f"{deg}{college}{grad}"
        elif onboard_data.role == "Working Professional":
            desig = onboard_data.current_designation or "Professional"
            comp = f" at {onboard_data.current_company}" if onboard_data.current_company else ""
            exp = f" ({onboard_data.years_of_experience} Experience)" if onboard_data.years_of_experience else ""
            edu = f"{desig}{comp}{exp}"
        elif onboard_data.role == "Career Switcher":
            dom = onboard_data.current_domain or "Non-Tech Field"
            comp = f" (Currently at {onboard_data.current_company})" if onboard_data.current_company else ""
            exp = f" | {onboard_data.years_of_experience} in {dom}" if onboard_data.years_of_experience else f" | Background: {dom}"
            edu = f"Transitioning from {dom}{comp}{exp}"
            
    if not sem or sem.strip() == "":
        if onboard_data.role == "Student":
            sem_str = onboard_data.semester or "Undergraduate"
            cgpa_str = f" (CGPA: {onboard_data.cgpa})" if onboard_data.cgpa else ""
            sem = f"{sem_str}{cgpa_str}"
        elif onboard_data.role == "Working Professional":
            notice = f"Notice: {onboard_data.notice_period}" if onboard_data.notice_period else "Active Placement Prep"
            deg = f" | Degree: {onboard_data.highest_degree}" if onboard_data.highest_degree else ""
            sem = f"{notice}{deg}"
        elif onboard_data.role == "Career Switcher":
            goal = f"Goal: {onboard_data.switch_goal}" if onboard_data.switch_goal else "Tech Career Transition"
            timeline = f" | Timeline: {onboard_data.transition_timeline}" if onboard_data.transition_timeline else ""
            sem = f"{goal}{timeline}"

    current_user.education = edu
    current_user.semester = sem
    current_user.skills = onboard_data.skills or []
    current_user.languages_known = onboard_data.languages_known or []
    current_user.experience_level = onboard_data.experience_level or "Beginner"
    current_user.preferred_learning_hours = onboard_data.preferred_learning_hours or 2
    current_user.expected_placement_date = onboard_data.expected_placement_date or "Within 6 Months"
    current_user.target_roles = onboard_data.target_roles or ["Software Engineer"]
    
    current_user.profile_details = {k: v for k, v in onboard_data.model_dump().items() if v not in (None, "", [])}
    flag_modified(current_user, "profile_details")
    flag_modified(current_user, "skills")
    flag_modified(current_user, "languages_known")
    flag_modified(current_user, "target_roles")
    
    # Award XP for onboarding completion!
    if current_user.xp == 0:
        current_user.xp = 100
        current_user.level = 1
        
        # Add welcome notification
        welcome_notif = models.Notification(
            user_id=current_user.id,
            title="Profile Ready! (+100 XP)",
            message=f"Welcome to GapX AI, {current_user.full_name or 'Scholar'}! Your profile has been initialized for the '{current_user.role}' track. Start completing your 8-Stage Roadmap to master your skills!",
            type="Achievement"
        )
        db.add(welcome_notif)

    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    users = db.query(models.User).order_by(models.User.xp.desc()).limit(10).all()
    
    leaderboard = []
    for idx, u in enumerate(users):
        leaderboard.append({
            "rank": idx + 1,
            "name": u.full_name or "Anonymous Scholar",
            "xp": u.xp,
            "level": u.level,
            "role": u.role,
            "streak": u.streak
        })
    return leaderboard

@router.get("/notifications", response_model=List[dict])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    notifications = db.query(models.Notification)\
        .filter(models.Notification.user_id == current_user.id)\
        .order_by(models.Notification.created_at.desc())\
        .limit(20).all()
        
    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "type": n.type,
            "created_at": n.created_at
        } for n in notifications
    ]

@router.post("/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    notif = db.query(models.Notification)\
        .filter(models.Notification.id == notif_id, models.Notification.user_id == current_user.id)\
        .first()
        
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notif.is_read = True
    db.commit()
    return {"message": "Notification marked as read"}
