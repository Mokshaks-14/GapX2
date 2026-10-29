from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.judge0 import CodeExecutionService
from app.services.ai_service import AIService
from app.services.gamification import record_activity
import random

router = APIRouter(prefix="/coding", tags=["Coding Practice Module"])

@router.get("/problems", response_model=List[schemas.CodingProblemListResponse])
def list_problems(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    problems = db.query(models.CodingProblem).all()
    
    # Get user solved problem IDs
    solved_submissions = db.query(models.CodingSubmission)\
        .filter(models.CodingSubmission.user_id == current_user.id, models.CodingSubmission.status == "Accepted")\
        .all()
    solved_ids = {s.problem_id for s in solved_submissions}
    
    return [
        schemas.CodingProblemListResponse(
            id=p.id,
            title=p.title,
            difficulty=p.difficulty,
            category=p.category,
            company_tags=p.company_tags or ["Top Tech"],
            is_solved=(p.id in solved_ids)
        ) for p in problems
    ]

def public_problem(p: models.CodingProblem) -> schemas.CodingProblemBase:
    """Problem details without hidden test cases."""
    data = schemas.CodingProblemBase.model_validate(p, from_attributes=True).model_dump()
    tests = p.test_cases or []
    data["test_cases"] = [{"input": t.get("input", ""), "output": t.get("output", "")} for t in tests if not t.get("is_hidden")]
    data["hidden_test_count"] = sum(1 for t in tests if t.get("is_hidden"))
    data["company_tags"] = p.company_tags or []
    data["hints"] = p.hints or []
    return schemas.CodingProblemBase(**data)

@router.get("/problems/{prob_id}", response_model=schemas.CodingProblemBase)
def get_problem(
    prob_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    p = db.query(models.CodingProblem).filter(models.CodingProblem.id == prob_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Problem not found")
    return public_problem(p)

@router.post("/problems/{prob_id}/run", response_model=schemas.CodeSubmitResponse)
def run_code(
    prob_id: int,
    req: schemas.CodeSubmitRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    p = db.query(models.CodingProblem).filter(models.CodingProblem.id == prob_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Problem not found")
        
    # Get only non-hidden test cases for simple runs
    public_tcs = [tc for tc in p.test_cases if not tc.get("is_hidden", False)]
    if not public_tcs:
        public_tcs = p.test_cases[:2] # Fallback to first two
        
    # Execute code
    res = CodeExecutionService.execute_code(req.code, req.language, public_tcs, p.signature)
    
    return schemas.CodeSubmitResponse(
        status=res["status"],
        execution_time=res["execution_time"],
        memory_usage=res["memory_usage"],
        message=res["message"],
        test_results=res["test_results"],
        ai_feedback=None,
        error_details=res.get("error_details")
    )

@router.post("/problems/{prob_id}/submit", response_model=schemas.CodeSubmitResponse)
def submit_code(
    prob_id: int,
    req: schemas.CodeSubmitRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    p = db.query(models.CodingProblem).filter(models.CodingProblem.id == prob_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Problem not found")
        
    # Run against ALL test cases (public and hidden)
    res = CodeExecutionService.execute_code(req.code, req.language, p.test_cases, p.signature)
    
    # Analyze code if there are bugs, using AI service
    ai_feedback = None
    if res["status"] != "Accepted":
        hint_res = AIService.get_coding_hint(p.title, p.problem_statement, req.code, req.language, p.hints, p.editorial)
        ai_feedback = f"Hint: {hint_res.get('hint')}\nApproach: {hint_res.get('approach')}"
        
    # Save submission record
    submission = models.CodingSubmission(
        user_id=current_user.id,
        problem_id=p.id,
        code=req.code,
        language=req.language,
        status=res["status"],
        execution_time=res["execution_time"],
        memory_usage=res["memory_usage"],
        ai_feedback=ai_feedback
    )
    db.add(submission)
    
    # Award XP if solved successfully
    if res["status"] == "Accepted":
        # Check if already solved previously to avoid double XP farming
        prev_solved = db.query(models.CodingSubmission)\
            .filter(
                models.CodingSubmission.user_id == current_user.id,
                models.CodingSubmission.problem_id == p.id,
                models.CodingSubmission.status == "Accepted",
                models.CodingSubmission.id != submission.id
            ).first()
            
        if not prev_solved:
            xp_reward = 100 if p.difficulty == "Hard" else (50 if p.difficulty == "Medium" else 30)
            current_user.xp += xp_reward
            record_activity(current_user)
            
            # Level up check
            new_lvl = (current_user.xp // 500) + 1
            if new_lvl > current_user.level:
                current_user.level = new_lvl
                lvl_notif = models.Notification(
                    user_id=current_user.id,
                    title=f"Leveled Up! Level {new_lvl}",
                    message=f"You solved '{p.title}' and reached Level {new_lvl}! Earned +{xp_reward} XP.",
                    type="Achievement"
                )
                db.add(lvl_notif)
            else:
                db.add(models.Notification(
                    user_id=current_user.id,
                    title=f"Problem Solved! (+{xp_reward} XP)",
                    message=f"Successfully cleared all test cases for '{p.title}'. Excellent job!",
                    type="Coding"
                ))

    db.commit()
    
    return schemas.CodeSubmitResponse(
        status=res["status"],
        execution_time=res["execution_time"],
        memory_usage=res["memory_usage"],
        message=res["message"],
        test_results=res["test_results"],
        ai_feedback=ai_feedback,
        error_details=res.get("error_details")
    )

# --- DRAFT AUTO-SAVE ENDPOINTS ---
@router.get("/problems/{prob_id}/draft", response_model=schemas.CodeDraftResponse)
def get_code_draft(
    prob_id: int,
    language: str = "python",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    draft = db.query(models.CodingDraft)\
        .filter(
            models.CodingDraft.user_id == current_user.id,
            models.CodingDraft.problem_id == prob_id,
            models.CodingDraft.language == language
        ).first()
        
    if not draft:
        # Fall back to problem starter code
        p = db.query(models.CodingProblem).filter(models.CodingProblem.id == prob_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Problem not found")
        starter_map = {
            "python": p.starter_code_python or "# Write solution here\n",
            "java": p.starter_code_java or "// Write solution here\n",
            "cpp": p.starter_code_cpp or "// Write solution here\n",
            "javascript": p.starter_code_js or "// Write solution here\n"
        }
        return schemas.CodeDraftResponse(
            code=starter_map.get(language, "# Write solution here\n"),
            language=language,
            updated_at=None
        )
        
    return schemas.CodeDraftResponse(
        code=draft.code,
        language=draft.language,
        updated_at=draft.updated_at.isoformat() if draft.updated_at else None
    )

@router.post("/problems/{prob_id}/draft", response_model=schemas.CodeDraftResponse)
def save_code_draft(
    prob_id: int,
    req: schemas.CodeDraftRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    draft = db.query(models.CodingDraft)\
        .filter(
            models.CodingDraft.user_id == current_user.id,
            models.CodingDraft.problem_id == prob_id,
            models.CodingDraft.language == req.language
        ).first()
        
    if not db.query(models.CodingProblem.id).filter(models.CodingProblem.id == prob_id).first():
        raise HTTPException(status_code=404, detail="Problem not found")
    if draft:
        draft.code = req.code
    else:
        draft = models.CodingDraft(
            user_id=current_user.id,
            problem_id=prob_id,
            language=req.language,
            code=req.code
        )
        db.add(draft)
        
    db.commit()
    db.refresh(draft)
    return schemas.CodeDraftResponse(
        code=draft.code,
        language=draft.language,
        updated_at=draft.updated_at.isoformat() if draft.updated_at else None
    )

# --- AI HINTS & CONTEXTUAL FEEDBACK ---
@router.post("/problems/{prob_id}/ai-hint", response_model=schemas.AIHintResponse)
def get_smart_ai_hint(
    prob_id: int,
    req: schemas.AIHintRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    p = db.query(models.CodingProblem).filter(models.CodingProblem.id == prob_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Problem not found")
        
    all_hints = p.hints or [
        "Think about optimal time complexity.",
        "Consider using auxiliary data structures like HashMap, Stack, or Two Pointers.",
        "Ensure edge cases like empty arrays, single elements, and negative values are handled."
    ]
    
    idx = max(0, min(req.hint_level - 1, len(all_hints) - 1))
    current_hint = all_hints[idx]
    
    # If code is provided and hint_level >= 2, run AI code inspection
    code_analysis = None
    if req.code and len(req.code.strip()) > 30:
        hint_res = AIService.get_coding_hint(p.title, p.problem_statement, req.code, req.language, p.hints, p.editorial)
        code_analysis = hint_res.get("hint") or hint_res.get("approach")
        
    approach_desc = p.editorial or f"Use standard {p.category} technique to achieve {p.expected_time_complexity} time."
    
    return schemas.AIHintResponse(
        title=p.title,
        hints=all_hints,
        current_hint=current_hint,
        approach=approach_desc,
        code_analysis=code_analysis,
        edge_cases=[
            "Empty input or single element input",
            "Duplicate values in input collection",
            "Large inputs reaching max constraint (checking for TLE)"
        ]
    )

@router.get("/problems/{prob_id}/hint")
def get_hints(
    prob_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    p = db.query(models.CodingProblem).filter(models.CodingProblem.id == prob_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Problem not found")
        
    return {
        "hints": p.hints or ["Consider using double pointers to scan from ends.", "Analyze standard hash-map indexing options."]
    }

# --- TESTING MODULE ---
@router.post("/test/start", response_model=schemas.CodingTestResponse)
def start_coding_test(
    req: schemas.CodingTestCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Fetch random questions (e.g. 1 Easy, 1 Medium, 1 Hard depending on duration)
    problems = db.query(models.CodingProblem).all()
    if not problems:
        raise HTTPException(status_code=400, detail="No coding problems loaded in database.")
        
    if req.duration_minutes <= 30:
        # 1 Easy, 1 Medium
        test_problems = random.sample(problems, min(2, len(problems)))
    else:
        # 1 Easy, 2 Medium, 1 Hard
        test_problems = random.sample(problems, min(4, len(problems)))
        
    # Generate mock assessment ID
    test_id = f"test-{random.randint(100000, 999999)}"
    
    return schemas.CodingTestResponse(
        test_id=test_id,
        duration_minutes=req.duration_minutes,
        problems=[public_problem(p) for p in test_problems]
    )
