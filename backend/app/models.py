from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)          # admins can disable an account
    last_login_at = Column(DateTime, nullable=True)
    
    # Onboarding properties
    role = Column(String, default="Student")  # Student, Working Professional, Career Switcher
    education = Column(String, nullable=True)
    semester = Column(String, nullable=True)
    skills = Column(JSON, default=list) # List of skills
    languages_known = Column(JSON, default=list)
    experience_level = Column(String, default="Beginner")
    preferred_learning_hours = Column(Integer, default=2)
    expected_placement_date = Column(String, nullable=True)
    target_roles = Column(JSON, default=list) # e.g. ["Software Engineer", "Frontend Developer"]
    # Everything entered during onboarding (college, CGPA, company, links, project, interests...)
    profile_details = Column(JSON, default=dict)
    
    # Gamification
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    streak = Column(Integer, default=0)
    last_active_date = Column(String, nullable=True)  # ISO date of last XP-earning activity (for daily streaks)
    badges = Column(JSON, default=list) # List of earned badge IDs/Names
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    roadmaps = relationship("Roadmap", back_populates="user", cascade="all, delete-orphan")
    submissions = relationship("CodingSubmission", back_populates="user", cascade="all, delete-orphan")
    interviews = relationship("MockInterview", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=True)
    
    # Analysis results
    ats_score = Column(Integer, default=0)
    resume_score = Column(Integer, default=0)
    strengths = Column(JSON, default=list)
    weaknesses = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    missing_keywords = Column(JSON, default=list)
    suggestions = Column(JSON, default=list)
    readiness_level = Column(String, default="Beginner") # Beginner, Intermediate, Placement-Ready
    
    # Structured resume data (generated or parsed)
    resume_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="resumes")

class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_role = Column(String, nullable=False)
    progress_percentage = Column(Float, default=0.0)
    
    # JSON content containing stages, topics, checklists, resources, and problems
    stages_data = Column(JSON, nullable=False)
    
    estimated_completion_date = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="roadmaps")

class CodingProblem(Base):
    __tablename__ = "coding_problems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    difficulty = Column(String, default="Easy") # Easy, Medium, Hard
    category = Column(String, nullable=False) # e.g. "Arrays", "DP"
    problem_statement = Column(Text, nullable=False)
    constraints = Column(Text, nullable=True)
    input_format = Column(Text, nullable=True)
    output_format = Column(Text, nullable=True)
    example_input = Column(Text, nullable=True)
    example_output = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    expected_time_complexity = Column(String, default="O(N)")
    expected_space_complexity = Column(String, default="O(1)")
    company_tags = Column(JSON, default=list) # e.g. ["Google", "Amazon", "Meta"]
    
    # Code templates
    starter_code_python = Column(Text, nullable=True)
    starter_code_java = Column(Text, nullable=True)
    starter_code_cpp = Column(Text, nullable=True)
    starter_code_c = Column(Text, nullable=True)
    starter_code_js = Column(Text, nullable=True)
    
    # Test cases: List of dicts, e.g. [{"input": "...", "output": "...", "is_hidden": false}]
    test_cases = Column(JSON, nullable=False)
    hints = Column(JSON, default=list) # List of string hints
    editorial = Column(Text, nullable=True)
    # How the test runner calls the solution: {"fn": "twoSum", "params": [["nums", "int[]"], ...], "returns": "int[]"}
    signature = Column(JSON, nullable=True)
    # Problems added from the admin panel (built-in ones come from the problem bank)
    is_custom = Column(Boolean, default=False)
    created_by = Column(String, nullable=True)
    
    submissions = relationship("CodingSubmission", back_populates="problem", cascade="all, delete-orphan")

class CodingSubmission(Base):
    __tablename__ = "coding_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    problem_id = Column(Integer, ForeignKey("coding_problems.id"), nullable=False)
    
    code = Column(Text, nullable=False)
    language = Column(String, nullable=False) # python, java, cpp, javascript
    status = Column(String, default="Pending") # Accepted, Wrong Answer, Time Limit Exceeded, Compile Error
    execution_time = Column(Float, default=0.0) # in ms
    memory_usage = Column(Float, default=0.0) # in KB
    ai_feedback = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="submissions")
    problem = relationship("CodingProblem", back_populates="submissions")

class CodingDraft(Base):
    __tablename__ = "coding_drafts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    problem_id = Column(Integer, ForeignKey("coding_problems.id"), nullable=False)
    language = Column(String, nullable=False, default="python")
    code = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    problem = relationship("CodingProblem")

class MockInterview(Base):
    __tablename__ = "mock_interviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_role = Column(String, nullable=False)
    experience_level = Column(String, default="Entry Level")
    interview_type = Column(String, default="Mixed") # Technical, HR, Behavioral, Managerial, Mixed
    
    # Transcript: List of chat messages, e.g. [{"role": "interviewer", "text": "..."}, {"role": "candidate", "text": "..."}]
    transcript = Column(JSON, default=list)
    
    # Detailed feedback: strengths, weaknesses, ideal answers, improvements
    feedback = Column(JSON, default=dict)
    
    # Scores
    technical_score = Column(Integer, default=0)
    communication_score = Column(Integer, default=0)
    confidence_score = Column(Integer, default=0)
    problem_solving_score = Column(Integer, default=0)
    leadership_score = Column(Integer, default=0)
    overall_score = Column(Integer, default=0)
    
    # Webcam/Behavior scores (attention, eye contact, smile, engagement)
    behavior_scores = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="interviews")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    type = Column(String, default="Info") # DailyGoal, Roadmap, Coding, Interview, Achievement
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="notifications")


class EmailVerification(Base):
    """One-time sign-up codes (stored hashed)."""
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    code_hash = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    attempts = Column(Integer, default=0)
    last_sent_at = Column(DateTime, nullable=True)
    window_start = Column(DateTime, nullable=True)
    sends_in_window = Column(Integer, default=0)


class InterviewQuestion(Base):
    """Technical interview questions added from the admin panel; merged into the question bank."""
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    track = Column(String, index=True, nullable=False)      # frontend, backend, sde, ...
    topic = Column(String, nullable=False)
    level = Column(String, default="Medium")                 # Easy, Medium, Hard
    question = Column(Text, nullable=False)
    key_points = Column(JSON, default=list)                  # [["hash map", "dictionary", "hashmap"], ...]
    ideal_answer = Column(Text, nullable=False)
    hint = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """Security and activity events shown in the admin panel."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    category = Column(String, index=True, nullable=False)   # auth, interview, integrity, coding, resume, admin
    event = Column(String, nullable=False)                   # e.g. login_failed, phone_detected
    severity = Column(String, default="info", index=True)    # info, warning, critical
    user_id = Column(Integer, nullable=True, index=True)
    user_email = Column(String, nullable=True, index=True)
    ip_address = Column(String, nullable=True)
    details = Column(JSON, default=dict)
