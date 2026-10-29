from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

# --- AUTH SCHEMAS ---
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class GoogleLoginRequest(BaseModel):
    credential: str  # Google Identity Services ID token

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    full_name: Optional[str]
    email: str

# --- ONBOARDING SCHEMAS ---
class UserOnboard(BaseModel):
    role: str
    education: Optional[str] = None
    semester: Optional[str] = None
    skills: List[str] = []
    languages_known: List[str] = []
    experience_level: Optional[str] = "Beginner"
    preferred_learning_hours: Optional[int] = 2
    expected_placement_date: Optional[str] = None
    target_roles: List[str] = []
    
    # Dynamic profile parameters
    college_name: Optional[str] = None
    degree_branch: Optional[str] = None
    cgpa: Optional[float] = None
    graduation_year: Optional[str] = None
    current_company: Optional[str] = None
    current_designation: Optional[str] = None
    years_of_experience: Optional[str] = None
    notice_period: Optional[str] = None
    highest_degree: Optional[str] = None
    current_domain: Optional[str] = None
    transition_timeline: Optional[str] = None
    switch_goal: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_admin: bool = False
    role: str
    education: Optional[str]
    semester: Optional[str]
    skills: List[str]
    languages_known: List[str]
    experience_level: str
    preferred_learning_hours: int
    expected_placement_date: Optional[str]
    target_roles: List[str]
    xp: int
    level: int
    streak: int
    badges: List[str]
    created_at: datetime

    class Config:
        from_attributes = True

# --- RESUME SCHEMAS ---
class ManualResumeCreate(BaseModel):
    name: str
    headline: Optional[str] = "Software Engineer"
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    summary: Optional[str] = None
    education: Optional[str] = None
    college: Optional[str] = None
    semester: Optional[str] = None
    cgpa: Optional[Union[float, str]] = None
    education_items: Optional[List[Dict[str, Any]]] = None
    skills: List[str] = []
    languages: List[str] = []
    frameworks: Optional[List[str]] = []
    tools: Optional[List[str]] = []
    experience: Optional[List[Dict[str, Any]]] = None
    internships: Optional[List[Dict[str, Any]]] = None
    projects: Optional[List[Dict[str, Any]]] = None
    certifications: Optional[List[str]] = []
    achievements: Optional[List[str]] = []
    hackathons: Optional[List[str]] = []
    interests: Optional[List[str]] = []
    is_fresher: Optional[bool] = None

class ResumeSummaryResponse(BaseModel):
    summary: str

class ResumeAnalysisResponse(BaseModel):
    ats_score: int
    resume_score: int
    strengths: List[str]
    weaknesses: List[str]
    missing_skills: List[str]
    missing_keywords: List[str]
    suggestions: List[str]
    readiness_level: str
    parsed_name: Optional[str] = None
    parsed_email: Optional[str] = None
    parsed_phone: Optional[str] = None
    parsed_links: Optional[Dict[str, str]] = None
    parsed_education: Optional[List[Dict[str, Any]]] = None
    parsed_experience: Optional[List[Dict[str, Any]]] = None
    parsed_projects: Optional[List[Dict[str, Any]]] = None
    parsed_skills: Optional[Dict[str, List[str]]] = None
    parsed_certifications: Optional[List[str]] = None
    score_breakdown: Optional[Dict[str, int]] = None

# --- ROADMAP SCHEMAS ---
class RoadmapResponse(BaseModel):
    id: int
    target_role: str
    progress_percentage: float
    stages_data: List[Dict[str, Any]]
    estimated_completion_date: Optional[str]

    class Config:
        from_attributes = True

class ToggleTopicRequest(BaseModel):
    stage_id: Any
    topic_id: Any
    is_completed: bool

# --- CODING PROBLEMS & SUBMISSIONS ---
class CodingProblemBase(BaseModel):
    id: int
    title: str
    difficulty: str
    category: str
    problem_statement: str
    constraints: Optional[str]
    input_format: Optional[str]
    output_format: Optional[str]
    example_input: Optional[str]
    example_output: Optional[str]
    explanation: Optional[str]
    expected_time_complexity: str
    expected_space_complexity: str
    company_tags: List[str] = []
    starter_code_python: Optional[str]
    starter_code_java: Optional[str]
    starter_code_cpp: Optional[str]
    starter_code_c: Optional[str] = None
    starter_code_js: Optional[str]
    hints: List[str]
    editorial: Optional[str] = None
    test_cases: List[Dict[str, Any]] = []  # public examples only; hidden cases never leave the server
    hidden_test_count: int = 0

    class Config:
        from_attributes = True

class CodingProblemListResponse(BaseModel):
    id: int
    title: str
    difficulty: str
    category: str
    company_tags: List[str] = []
    is_solved: bool = False

class CodeSubmitRequest(BaseModel):
    code: str
    language: str

class CodeSubmitResponse(BaseModel):
    status: str
    execution_time: float
    memory_usage: float
    message: str
    test_results: List[Dict[str, Any]]
    ai_feedback: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

class CodeDraftRequest(BaseModel):
    code: str
    language: str

class CodeDraftResponse(BaseModel):
    code: str
    language: str
    updated_at: Optional[str] = None

class AIHintRequest(BaseModel):
    code: Optional[str] = None
    language: Optional[str] = "python"
    hint_level: Optional[int] = 1

class AIHintResponse(BaseModel):
    title: str
    hints: List[str]
    current_hint: str
    approach: str
    code_analysis: Optional[str] = None
    edge_cases: List[str] = []

class CodingTestCreateRequest(BaseModel):
    duration_minutes: int # 30, 60, 90, 120

class CodingTestResponse(BaseModel):
    test_id: str
    duration_minutes: int
    problems: List[CodingProblemBase]

# --- MOCK INTERVIEW SCHEMAS ---
class InterviewStartRequest(BaseModel):
    target_role: str
    experience_level: str
    interview_type: str  # Technical, HR, Mixed
    job_description: Optional[str] = None
    specific_skills: Optional[List[str]] = None
    track: Optional[str] = None          # frontend, backend, fullstack, sde, data_science, ml, devops, mobile, data_analyst, security
    topic_domain: Optional[str] = None   # legacy alias for track
    num_questions: Optional[int] = 8

class InterviewStartResponse(BaseModel):
    interview_id: int
    first_question: str
    speech_text: Optional[str] = None
    difficulty: Optional[str] = "Easy"
    phase: Optional[str] = None
    track: Optional[str] = None
    track_label: Optional[str] = None
    total_questions: Optional[int] = None

class InterviewMessageRequest(BaseModel):
    answer: str
    audio_response: Optional[bool] = False
    # Face-analysis metrics (0..1) from the browser. Omitted when the camera is off or analysis is unavailable.
    attention_metric: Optional[float] = None
    smile_metric: Optional[float] = None
    stress_metric: Optional[float] = None
    eye_contact_metric: Optional[float] = None
    wpm_metric: Optional[int] = None
    filler_words_count: Optional[int] = None
    current_difficulty: Optional[str] = None
    topic_domain: Optional[str] = None

class InterviewMessageResponse(BaseModel):
    next_question: Optional[str]  # None when finished
    is_finished: bool
    is_repeat: bool = False
    ai_immediate_feedback: Optional[str] = None
    is_correct: Optional[bool] = True
    ai_correction: Optional[str] = None
    ideal_answer: Optional[str] = None
    speech_text_to_speak: Optional[str] = None
    current_live_score: Optional[int] = None
    confidence_metric: Optional[int] = None
    difficulty: Optional[str] = "Easy"
    difficulty_change: Optional[str] = "same"
    phase: Optional[str] = None
    question_kind: Optional[str] = None
    question_number: Optional[int] = None
    total_questions: Optional[int] = None
    turn_score: Optional[int] = None

class InterviewFeedbackResponse(BaseModel):
    id: int
    target_role: str
    interview_type: str
    technical_score: int
    communication_score: int
    confidence_score: int
    problem_solving_score: int
    leadership_score: Optional[int] = 75
    overall_score: int
    feedback: Dict[str, Any]
    behavior_scores: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

# --- CAREER MENTOR SCHEMAS ---
class MentorMessageRequest(BaseModel):
    message: str
    history: List[Dict[str, str]]

class MentorMessageResponse(BaseModel):
    response: str
    suggestions: List[str]

# --- DASHBOARD METRICS ---
class DashboardMetricsResponse(BaseModel):
    placement_readiness_score: int
    placement_probability: str
    roadmap_progress: float
    coding_progress: float
    questions_solved: int
    coding_accuracy: float
    interview_scores: List[Dict[str, Any]]
    communication_score: int
    confidence_score: int
    resume_score: int
    skill_gap: List[Dict[str, Any]]
    learning_hours: int
    streak: int
    xp: int
    level: int
    daily_goals: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    recommended_companies: List[str]
    remaining_weak_areas: List[str]
