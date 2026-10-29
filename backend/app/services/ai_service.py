"""AI features that are not interview- or roadmap-specific: resume review, mentor chat, coding hints.

Every method tries a hosted LLM first (see llm.py) and falls back to GapX's offline engines.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.services import llm
from app.services.career_knowledge import CareerKnowledgeEngine
from app.services.resume_parser import ResumeEntityExtractor

logger = logging.getLogger(__name__)


class AIService:

    # ── RESUME ────────────────────────────────────────────────────────────────
    @staticmethod
    def analyze_resume(resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Scores a parsed or manually entered resume against the candidate's target role."""
        resume_data = resume_data or {}
        raw_text = str(resume_data.get("extracted_text") or "")
        target_roles = resume_data.get("target_roles") or []
        if isinstance(target_roles, list) and target_roles and target_roles[0]:
            primary_role = str(target_roles[0])
        else:
            primary_role = str(resume_data.get("headline") or "Software Engineer")

        entities = ResumeEntityExtractor.extract_text_entities(raw_text, resume_data)
        audit = ResumeEntityExtractor.evaluate_and_audit(entities, primary_role)

        if llm.is_available():
            prompt = f"""
You are an ATS screening system and senior technical recruiter hiring for {primary_role}.
Candidate profile:
- Name: {entities.get('name')}
- Skills: {json.dumps(entities.get('skills_by_category'))}
- Projects: {json.dumps(entities.get('projects'))}
- Experience: {json.dumps(entities.get('experience'))}
- Education: {json.dumps(entities.get('education'))}
- Resume text (truncated): {raw_text[:2500]}

Return STRICT JSON:
{{"ats_score": 0-100, "resume_score": 0-100,
  "strengths": [3-5 strengths that cite their actual projects/skills],
  "weaknesses": [3-5 gaps for {primary_role}],
  "missing_skills": [3-5 skills], "missing_keywords": [6-8 keywords],
  "suggestions": [3-4 specific, actionable fixes],
  "readiness_level": "Placement-Ready" | "Competitive Candidate" | "Intermediate / Developing" | "Needs Refinement"}}
"""
            parsed = llm.generate_json(prompt)
            if isinstance(parsed, dict) and "ats_score" in parsed:
                for key in ("ats_score", "resume_score"):
                    try:
                        audit[key] = int(min(max(int(parsed.get(key, audit[key])), 0), 100))
                    except (TypeError, ValueError):
                        pass
                for key in ("strengths", "weaknesses", "missing_skills", "missing_keywords", "suggestions"):
                    if isinstance(parsed.get(key), list) and parsed[key]:
                        audit[key] = [str(x) for x in parsed[key]]
                if parsed.get("readiness_level"):
                    audit["readiness_level"] = str(parsed["readiness_level"])
        return audit

    @staticmethod
    def write_resume_summary(profile: Dict[str, Any]) -> str:
        """Writes a 2-3 sentence ATS-friendly professional summary from the candidate's profile."""
        role = profile.get("headline") or "Software Engineer"
        skills = [s for s in (profile.get("skills") or []) if s][:6]
        projects = profile.get("projects") or []
        experience = profile.get("experience") or []
        education = profile.get("education") or ""
        interests = [i for i in (profile.get("interests") or []) if i][:3]

        if llm.is_available():
            prompt = f"""
Write a professional resume summary (2-3 sentences, max 60 words, first person implied, no "I") for a {role} candidate.
Use only facts given here; do not invent employers, numbers or degrees.
Education: {education}
Skills: {', '.join(skills)}
Projects: {json.dumps(projects)[:800]}
Experience: {json.dumps(experience)[:800]}
Interests: {', '.join(interests)}
Return plain text only.
"""
            text = llm.generate_text(prompt)
            if text:
                return re.sub(r"\s+", " ", text.strip().strip('"'))

        # Offline template built only from the user's own data
        parts = []
        lead = f"{role} candidate"
        if education:
            lead += f" with a background in {education}"
        if skills:
            lead += f", skilled in {', '.join(skills[:-1]) + ' and ' + skills[-1] if len(skills) > 1 else skills[0]}"
        parts.append(lead + ".")
        if experience:
            exp = experience[0]
            parts.append(f"Experience as {exp.get('role') or 'an engineer'}{' at ' + exp['company'] if exp.get('company') else ''}, delivering production features end to end.")
        elif projects:
            names = [p.get("name") or p.get("title") for p in projects if p.get("name") or p.get("title")]
            if names:
                parts.append(f"Built hands-on projects including {', '.join(names[:2])}, applying clean code, testing and version control.")
        else:
            parts.append("Strong grounding in data structures, algorithms and problem solving.")
        goal = f"Seeking a {role} role to build reliable, user-focused software"
        if interests:
            goal += f"; interested in {', '.join(interests)}"
        parts.append(goal + ".")
        return " ".join(parts)

    # ── AI MENTOR ─────────────────────────────────────────────────────────────
    @staticmethod
    def get_career_advice(query: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        history = history or []
        if not CareerKnowledgeEngine.is_in_scope(query):
            return {
                "response": CareerKnowledgeEngine.OUT_OF_SCOPE_MESSAGE,
                "suggestions": [
                    "How to prepare for technical interviews?",
                    "Solve Two Sum in Python",
                    "Tips to improve communication skills for interviews",
                ],
            }

        if llm.is_available():
            prompt = f"""You are GapX AI Mentor: an empathetic career coach and senior engineer.
Answer questions about interviews, coding, data structures & algorithms, computer science, any engineering subject, and communication skills.
If the question is unrelated (cooking, movies, sports, weather, medical, dating), reply exactly:
"I am designed only to answer questions related to interview, technical or communication skills only, so sorry I will not be able to answer this question."
For code: give complete, commented code plus time/space complexity. For career questions: give concrete frameworks (STAR, XYZ) and examples.
Format the answer in Markdown.

Return STRICT JSON: {{"response": "markdown answer", "suggestions": ["follow-up 1", "follow-up 2", "follow-up 3"]}}

Chat history: {json.dumps(history[-6:])}
User: {query}"""
            parsed = llm.generate_json(prompt)
            if isinstance(parsed, dict) and parsed.get("response"):
                return {
                    "response": str(parsed["response"]),
                    "suggestions": [str(s) for s in (parsed.get("suggestions") or [])][:3],
                }

        return CareerKnowledgeEngine.get_response(query, history)

    # ── CODING HINTS ──────────────────────────────────────────────────────────
    @staticmethod
    def get_coding_hint(problem_title: str, problem_statement: str, code: str, language: str,
                        hints: Optional[List[str]] = None, editorial: Optional[str] = None) -> Dict[str, str]:
        """Tutor-style hint about the user's code that does not hand over the full solution."""
        if llm.is_available():
            prompt = f"""A student is solving '{problem_title}' in {language}.
Problem:
{problem_statement}

Their code:
```{language}
{code}
```
Act as a LeetCode tutor. Point out the specific bug or inefficiency in THEIR code and the next step, without writing the corrected code.
Return JSON: {{"hint": "encouraging, specific hint", "approach": "the algorithm/idea needed"}}"""
            parsed = llm.generate_json(prompt)
            if isinstance(parsed, dict) and parsed.get("hint"):
                return {"hint": str(parsed["hint"]), "approach": str(parsed.get("approach", ""))}

        # Offline: use the problem's own curated hints and editorial rather than a generic message
        hint_list = [h for h in (hints or []) if h]
        hint = hint_list[min(1, len(hint_list) - 1)] if hint_list else \
            "Trace your code by hand on the first failing test case and compare each step with the expected output."
        approach = (editorial or "").strip().split("\n")[0][:400] if editorial else \
            "Start with a brute-force solution, then remove repeated work with a hash map, two pointers or sorting."
        return {"hint": hint, "approach": approach}
