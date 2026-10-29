from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.core.database import get_db
from app.core.security import get_admin_user
from typing import Dict, Any, List

router = APIRouter(prefix="/admin", tags=["Admin Control Panel"])

def check_admin(user: models.User = Depends(get_admin_user)):
    return user

@router.get("/metrics")
def get_admin_metrics(db: Session = Depends(get_db), admin: models.User = Depends(check_admin)):
    total_users = db.query(models.User).count()
    total_problems = db.query(models.CodingProblem).count()
    total_submissions = db.query(models.CodingSubmission).count()
    total_interviews = db.query(models.MockInterview).count()
    
    return {
        "total_users": total_users,
        "total_problems": total_problems,
        "total_submissions": total_submissions,
        "total_interviews": total_interviews,
        "active_roadmaps": db.query(models.Roadmap).count()
    }

@router.post("/problems")
def create_problem(
    payload: dict,
    db: Session = Depends(get_db),
    admin: models.User = Depends(check_admin)
):
    if not payload.get("title") or not payload.get("problem_statement"):
        raise HTTPException(status_code=400, detail="Title and problem statement are required.")
    db_problem = models.CodingProblem(
        title=payload.get("title"),
        difficulty=payload.get("difficulty", "Easy"),
        category=payload.get("category", "General"),
        problem_statement=payload.get("problem_statement"),
        constraints=payload.get("constraints"),
        input_format=payload.get("input_format"),
        output_format=payload.get("output_format"),
        example_input=payload.get("example_input"),
        example_output=payload.get("example_output"),
        explanation=payload.get("explanation"),
        expected_time_complexity=payload.get("expected_time_complexity", "O(N)"),
        expected_space_complexity=payload.get("expected_space_complexity", "O(1)"),
        starter_code_python=payload.get("starter_code_python"),
        starter_code_java=payload.get("starter_code_java"),
        starter_code_cpp=payload.get("starter_code_cpp"),
        starter_code_js=payload.get("starter_code_js"),
        test_cases=payload.get("test_cases", []),
        hints=payload.get("hints", [])
    )
    db.add(db_problem)
    db.commit()
    db.refresh(db_problem)
    return {"message": "Problem created successfully", "problem_id": db_problem.id}

@router.get("/users", response_model=List[schemas.UserResponse])
def get_all_users(db: Session = Depends(get_db), admin: models.User = Depends(check_admin)):
    return db.query(models.User).all()
