"""Compares a resume with a job description: keyword match score, matched and missing skills, tips."""
import re
from typing import Any, Dict, List

from app.services import llm
from app.services.interview_bank import TECH_LEXICON

EXTRA_TERMS = [
    "rest api", "rest apis", "microservices", "system design", "data structures", "algorithms", "oop", "unit testing", "testing",
    "ci/cd", "agile", "scrum", "git", "linux", "communication", "leadership", "problem solving", "debugging", "html", "css",
    "typescript", "next.js", "node.js", "express", "spring boot", "postgresql", "mysql", "mongodb", "redis", "kafka", "docker",
    "kubernetes", "aws", "azure", "gcp", "terraform", "jenkins", "graphql", "statistics", "a/b testing", "excel", "power bi",
    "tableau", "pandas", "numpy", "scikit-learn", "pytorch", "tensorflow", "nlp", "llm", "rag", "computer vision", "spark",
    "airflow", "etl", "data visualization", "machine learning", "deep learning", "security", "owasp", "networking", "jira",
    "figma", "accessibility", "performance optimization", "c", "c++", "java", "python", "javascript", "go", "kotlin", "swift",
    "flutter", "react native", "android", "ios", "sql", "nosql", "fastapi", "django", "flask", "react", "angular", "vue",
]
ALIASES = {"js": "javascript", "ts": "typescript", "nodejs": "node.js", "node": "node.js", "postgres": "postgresql",
           "k8s": "kubernetes", "ml": "machine learning", "dl": "deep learning", "nextjs": "next.js", "sklearn": "scikit-learn",
           "golang": "go", "rest": "rest api", "restful": "rest api", "ci cd": "ci/cd", "springboot": "spring boot"}
VOCAB = sorted(set(t.strip() for t in TECH_LEXICON + EXTRA_TERMS), key=len, reverse=True)


def _terms(text: str) -> List[str]:
    t = " " + re.sub(r"\s+", " ", (text or "").lower()) + " "
    for k, v in ALIASES.items():
        t = re.sub(rf"(?<![a-z0-9]){re.escape(k)}(?![a-z0-9])", v, t)
    found = []
    for term in VOCAB:
        if re.search(rf"(?<![a-z0-9+#]){re.escape(term)}(?![a-z0-9+#])", t) and not any(term in f for f in found):
            found.append(term)
    return found


def resume_text(data: Dict[str, Any]) -> str:
    parts = [str(data.get(k) or "") for k in ("headline", "summary", "education", "extracted_text")]
    for k in ("skills", "languages", "frameworks", "tools", "certifications", "achievements"):
        v = data.get(k) or []
        parts.append(", ".join(v) if isinstance(v, list) else str(v))
    for group in ("projects", "experience"):
        for item in data.get(group) or []:
            if isinstance(item, dict):
                parts += [str(item.get(x) or "") for x in ("name", "title", "role", "stack", "description")]
                bullets = item.get("bullets") or []
                parts.append(" ".join(bullets) if isinstance(bullets, list) else str(bullets))
    return "\n".join(parts)


def match(resume: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    jd_terms = _terms(job_description)
    res_terms = set(_terms(resume_text(resume)))
    matched = [t for t in jd_terms if t in res_terms]
    missing = [t for t in jd_terms if t not in res_terms]
    score = round(100 * len(matched) / len(jd_terms)) if jd_terms else 0
    tips = []
    if missing:
        tips.append(f"If you genuinely have these skills, add them to your Skills section or project bullets: {', '.join(missing[:6])}.")
    if score < 60:
        tips.append("Mirror the job's wording in your summary and project bullets (ATS systems match exact terms).")
    if not any(re.search(r"\d", b) for p in resume.get("projects") or [] if isinstance(p, dict) for b in (p.get("bullets") or [])):
        tips.append("Add numbers to your project bullets (users, speed-up, accuracy). Recruiters scan for measurable impact.")
    if score >= 80:
        tips.append("Strong match. Tailor your summary's first line to this role and apply.")

    result = {"match_score": score, "matched_keywords": matched, "missing_keywords": missing, "suggestions": tips,
              "verdict": "Strong match" if score >= 75 else "Good match" if score >= 55 else "Needs tailoring"}
    if llm.is_available() and job_description.strip():
        extra = llm.generate_json(fast=True, prompt=f"""A candidate's resume:
{resume_text(resume)[:2500]}

Job description:
{job_description[:2500]}

Return STRICT JSON: {{"summary": "2 sentences on how well they fit and the biggest gap",
"rewrite_tips": ["3 specific bullet rewrites or additions that would better match this job, only using facts from the resume"]}}""")
        if isinstance(extra, dict):
            if extra.get("summary"):
                result["ai_summary"] = str(extra["summary"])
            if isinstance(extra.get("rewrite_tips"), list):
                result["suggestions"] = result["suggestions"] + [str(x) for x in extra["rewrite_tips"][:3]]
    return result
