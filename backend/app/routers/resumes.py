from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app import models, schemas
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.ai_service import AIService
from app.services.pdf_generator import PDFResumeGenerator, PDFExtractor
from typing import Any, List, Dict, Optional
import json
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["Resume Modules"])

def validate_profile_links(linkedin: str = None, github: str = None):
    """Validates that provided LinkedIn and GitHub URLs match authentic profile structures."""
    if linkedin and linkedin.strip():
        clean_li = linkedin.strip().lower()
        if not re.search(r'(https?:\/\/)?(www\.)?linkedin\.com\/in\/[a-zA-Z0-9_\-\.\/]+', clean_li):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid LinkedIn profile link. Please provide a verified URL (e.g., https://linkedin.com/in/username)."
            )
    if github and github.strip():
        clean_gh = github.strip().lower()
        if not re.search(r'(https?:\/\/)?(www\.)?github\.com\/[a-zA-Z0-9_\-\.\/]+', clean_gh):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GitHub profile link. Please provide a verified URL (e.g., https://github.com/username)."
            )

@router.post("/upload", response_model=schemas.ResumeAnalysisResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF resume files (.pdf) are supported currently."
        )
        
    # Read and extract text from PDF using multi-engine PDFExtractor
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded resume file: {str(e)}"
        )
        
    raw_text = PDFExtractor.extract_text(contents)
    
    resume_text_sim = {
        "filename": file.filename,
        "is_uploaded_pdf": True,
        "name": current_user.full_name or "Candidate",
        "email": current_user.email,
        "extracted_text": raw_text,
        "target_roles": current_user.target_roles or ["Software Engineer"]
    }
        
    # Perform AI analysis
    analysis = AIService.analyze_resume(resume_text_sim)
    
    # Save to database
    db_resume = models.Resume(
        user_id=current_user.id,
        filename=file.filename,
        ats_score=analysis["ats_score"],
        resume_score=analysis["resume_score"],
        strengths=analysis["strengths"],
        weaknesses=analysis["weaknesses"],
        missing_skills=analysis["missing_skills"],
        missing_keywords=analysis["missing_keywords"],
        suggestions=analysis["suggestions"],
        readiness_level=analysis["readiness_level"],
        resume_data=analysis
    )
    first_resume = db.query(models.Resume).filter(models.Resume.user_id == current_user.id).count() == 0
    db.add(db_resume)

    # XP only for the first resume so repeated uploads can't be farmed
    if first_resume:
        current_user.xp += 150
        current_user.level = max(current_user.level, current_user.xp // 500 + 1)
    notif = models.Notification(
        user_id=current_user.id,
        title="Resume Analyzed!" + (" (+150 XP)" if first_resume else ""),
        message=f"Your resume '{file.filename}' was analyzed successfully. Your ATS score is {analysis['ats_score']}/100. Review missing skills and keywords on your resume panel.",
        type="Achievement"
    )
    db.add(notif)
    
    db.commit()
    return analysis

@router.post("/manual", response_model=schemas.ResumeAnalysisResponse)
def create_manual_resume(
    resume_in: schemas.ManualResumeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Validate verified social/portfolio profiles
    validate_profile_links(resume_in.linkedin, resume_in.github)
    
    # Convert manual form input to dict
    resume_data_dict = resume_in.model_dump()
    if not resume_data_dict.get("email"):
        resume_data_dict["email"] = current_user.email
    if not resume_data_dict.get("name"):
        resume_data_dict["name"] = current_user.full_name or "Candidate"
    
    # Run AI analysis on user-provided profile
    analysis = AIService.analyze_resume(resume_data_dict)
    
    # Save to db
    db_resume = models.Resume(
        user_id=current_user.id,
        filename="GapX_Standard_Resume.pdf",
        ats_score=analysis["ats_score"],
        resume_score=analysis["resume_score"],
        strengths=analysis["strengths"],
        weaknesses=analysis["weaknesses"],
        missing_skills=analysis["missing_skills"],
        missing_keywords=analysis["missing_keywords"],
        suggestions=analysis["suggestions"],
        readiness_level=analysis["readiness_level"],
        resume_data=analysis
    )
    first_resume = db.query(models.Resume).filter(models.Resume.user_id == current_user.id).count() == 0
    db.add(db_resume)

    if first_resume:
        current_user.xp += 150
        current_user.level = max(current_user.level, current_user.xp // 500 + 1)
    notif = models.Notification(
        user_id=current_user.id,
        title="ATS Resume Generated!" + (" (+150 XP)" if first_resume else ""),
        message=f"Your standard ATS-optimized resume has been generated with an ATS Compatibility Score of {analysis['ats_score']}/100! You can download the PDF anytime.",
        type="Achievement"
    )
    db.add(notif)
    
    db.commit()
    return analysis

@router.post("/generate-summary", response_model=schemas.ResumeSummaryResponse)
def generate_resume_summary(resume_in: schemas.ManualResumeCreate, current_user: models.User = Depends(get_current_user)):
    """Writes a professional summary (introduction) from the candidate's own resume details."""
    data = resume_in.model_dump()
    if not data.get("headline") and current_user.target_roles:
        data["headline"] = current_user.target_roles[0]
    return {"summary": AIService.write_resume_summary(data)}

@router.post("/download-pdf")
def download_resume_pdf_post(
    resume_in: schemas.ManualResumeCreate,
    current_user: models.User = Depends(get_current_user)
):
    validate_profile_links(resume_in.linkedin, resume_in.github)
    data = resume_in.model_dump()
    if not data.get("email"):
        data["email"] = current_user.email
    if not data.get("name"):
        data["name"] = current_user.full_name or "Candidate"
        
    pdf_buffer = PDFResumeGenerator.generate_resume_pdf(data)
    name = (data.get("name") or "Candidate").replace(" ", "_")
    filename = f"{name}_Standard_Resume.pdf"
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

@router.get("/download-pdf")
def download_latest_resume_pdf(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    resume = db.query(models.Resume)\
        .filter(models.Resume.user_id == current_user.id)\
        .order_by(models.Resume.created_at.desc())\
        .first()
        
    resume_data = {}
    if resume and resume.resume_data:
        resume_data = resume.resume_data
    else:
        # Fallback to current_user profile
        resume_data = {
            "name": current_user.full_name or "Candidate Scholar",
            "email": current_user.email,
            "headline": current_user.target_roles[0] if current_user.target_roles else "Software Engineer",
            "education": current_user.education or "Bachelor of Technology in Computer Science",
            "semester": current_user.semester or "Undergraduate",
            "skills": current_user.skills,
            "languages": current_user.languages_known,
            "summary": f"Motivated candidate preparing for {current_user.target_roles[0] if current_user.target_roles else 'Software Engineer'} roles. Proficient in data structures, system development, and problem solving."
        }
        
    pdf_buffer = PDFResumeGenerator.generate_resume_pdf(resume_data)
    name = (resume_data.get("name") or "Candidate").replace(" ", "_")
    filename = f"{name}_Standard_Resume.pdf"
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

def _normalize_edu(edu_data: Any) -> list:
    if not edu_data: return []
    if isinstance(edu_data, list):
        res = []
        for x in edu_data:
            if isinstance(x, dict):
                res.append({
                    "degree": x.get("degree") or x.get("title") or "Degree / Major",
                    "institution": x.get("institution") or x.get("college") or x.get("university") or "",
                    "cgpa": x.get("cgpa") or "",
                    "year": x.get("year") or x.get("dates") or ""
                })
            elif isinstance(x, str) and x.strip():
                res.append({"degree": x.strip(), "institution": "", "cgpa": "", "year": ""})
        return res
    elif isinstance(edu_data, str) and edu_data.strip():
        return [{"degree": edu_data.strip(), "institution": "", "cgpa": "", "year": ""}]
    elif isinstance(edu_data, dict):
        return [{
            "degree": edu_data.get("degree") or "Degree / Major",
            "institution": edu_data.get("institution") or "",
            "cgpa": edu_data.get("cgpa") or "",
            "year": edu_data.get("year") or ""
        }]
    return []

def _normalize_exp(exp_data: Any) -> list:
    if not exp_data: return []
    if isinstance(exp_data, list):
        res = []
        for x in exp_data:
            if isinstance(x, dict):
                res.append({
                    "role": x.get("role") or x.get("title") or "Software Engineer / Intern",
                    "company": x.get("company") or x.get("organization") or "",
                    "duration": x.get("duration") or x.get("dates") or "",
                    "description": x.get("description") or (x.get("bullets")[0] if x.get("bullets") else "")
                })
            elif isinstance(x, str) and x.strip():
                res.append({"role": x.strip(), "company": "", "duration": "", "description": ""})
        return res
    elif isinstance(exp_data, str) and exp_data.strip():
        return [{"role": exp_data.strip(), "company": "", "duration": "", "description": ""}]
    elif isinstance(exp_data, dict):
        return [{
            "role": exp_data.get("role") or "Software Engineer",
            "company": exp_data.get("company") or "",
            "duration": exp_data.get("duration") or "",
            "description": exp_data.get("description") or ""
        }]
    return []

def _normalize_proj(proj_data: Any) -> list:
    if not proj_data: return []
    if isinstance(proj_data, list):
        res = []
        for x in proj_data:
            if isinstance(x, dict):
                res.append({
                    "title": x.get("title") or x.get("name") or "Technical Project",
                    "stack": x.get("stack") or x.get("technologies") or "",
                    "description": x.get("description") or (x.get("bullets")[0] if x.get("bullets") else "")
                })
            elif isinstance(x, str) and x.strip():
                res.append({"title": x.strip(), "stack": "", "description": ""})
        return res
    elif isinstance(proj_data, str) and proj_data.strip():
        return [{"title": proj_data.strip(), "stack": "", "description": ""}]
    elif isinstance(proj_data, dict):
        return [{
            "title": proj_data.get("title") or "Technical Project",
            "stack": proj_data.get("stack") or "",
            "description": proj_data.get("description") or ""
        }]
    return []

@router.get("/latest", response_model=dict)
def get_latest_resume(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    resume = db.query(models.Resume)\
        .filter(models.Resume.user_id == current_user.id)\
        .order_by(models.Resume.created_at.desc())\
        .first()
        
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume profile found yet. Please upload one or build your resume."
        )
        
    res_data = resume.resume_data or {}
    return {
        "id": resume.id,
        "filename": resume.filename,
        "ats_score": resume.ats_score,
        "resume_score": resume.resume_score,
        "strengths": resume.strengths if isinstance(resume.strengths, list) else ([resume.strengths] if resume.strengths else []),
        "weaknesses": resume.weaknesses if isinstance(resume.weaknesses, list) else ([resume.weaknesses] if resume.weaknesses else []),
        "missing_skills": resume.missing_skills if isinstance(resume.missing_skills, list) else ([resume.missing_skills] if resume.missing_skills else []),
        "missing_keywords": resume.missing_keywords if isinstance(resume.missing_keywords, list) else ([resume.missing_keywords] if resume.missing_keywords else []),
        "suggestions": resume.suggestions if isinstance(resume.suggestions, list) else ([resume.suggestions] if resume.suggestions else []),
        "readiness_level": resume.readiness_level,
        "parsed_name": res_data.get("parsed_name") or res_data.get("name") or current_user.full_name,
        "parsed_email": res_data.get("parsed_email") or res_data.get("email") or current_user.email,
        "parsed_phone": res_data.get("parsed_phone") or res_data.get("phone"),
        "parsed_links": res_data.get("parsed_links") or {},
        "parsed_education": _normalize_edu(res_data.get("parsed_education") or res_data.get("education")),
        "parsed_experience": _normalize_exp(res_data.get("parsed_experience") or res_data.get("experience")),
        "parsed_projects": _normalize_proj(res_data.get("parsed_projects") or res_data.get("projects")),
        "parsed_skills": res_data.get("parsed_skills") or res_data.get("skills_by_category") or {},
        "parsed_certifications": res_data.get("parsed_certifications") or res_data.get("certifications") or [],
        "score_breakdown": res_data.get("score_breakdown") or {
            "keyword_match": 80, "experience_projects": 75, "formatting_structure": 85, "measurable_impact": 70
        },
        "resume_data": resume.resume_data,
        "created_at": resume.created_at
    }
