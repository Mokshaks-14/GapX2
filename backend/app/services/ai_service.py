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


OUT_OF_SCOPE_REPLY = ("I can only help with placement preparation, technical topics and using GapX, "
                      "so I can't answer that one.")


def _spoken_summary(markdown: str, max_words: int = 40) -> str:
    """A short, speakable version of an answer (no code or markdown)."""
    text = re.sub(r"```.*?```", " ", markdown or "", flags=re.S)
    text = re.sub(r"[#*_`>|]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.findall(r"[^.!?]+[.!?]", text) or [text]
    out, count = [], 0
    for sent in sentences:
        n = len(sent.split())
        if out and count + n > max_words:
            break
        out.append(sent.strip())
        count += n
    return " ".join(out)[:400]


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

    # ── AI MENTOR / ASSISTANT ─────────────────────────────────────────────────
    @staticmethod
    def get_career_advice(query: str, history: Optional[List[Dict[str, str]]] = None,
                          profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """A conversational assistant (via the configured LLM), personalised with the user's profile."""
        history = history or []
        if not CareerKnowledgeEngine.is_in_scope(query):  # obvious off-topic: answer instantly, no AI call
            return AIService._out_of_scope()
        if llm.is_available():
            context = ""
            if profile:
                context = "\n".join(f"- {k}: {v}" for k, v in profile.items() if v not in (None, "", [], {}))
            system = f"""You are GapX AI Coach, the assistant inside GapX, a placement-preparation app.

SCOPE: answer ONLY questions about what GapX helps with:
- coding, data structures & algorithms, and code in any language
- computer science and engineering subjects (OS, DBMS, networks, OOP, system design, ML/AI, web, cloud, security, maths for CS)
- placement and interview preparation (technical, HR, behavioral, aptitude), resumes, LinkedIn/GitHub profiles
- career guidance for tech roles, study plans and roadmaps, communication and soft skills for interviews
- how to use GapX features: Dashboard, AI Roadmap and notes, Resume builder and job-description match, Coding Practice, Mock Interview, daily challenge
For ANYTHING else (movies, sports, food, news, politics, health, relationships, general trivia, homework unrelated to tech careers, etc.)
reply with exactly this sentence and nothing else:
"{OUT_OF_SCOPE_REPLY}"

STYLE: warm, encouraging, like a senior mentor. Explain in simple words first, then add depth.
For code: complete, commented code plus time/space complexity. Use Markdown. Keep answers focused.

About the user (use it to personalise; don't recite it):
{{context}}

At the very end of every reply add two lines exactly in this format:
SPOKEN: <the key point of your answer in 1-2 natural spoken sentences, max 40 words, no markdown or code>
FOLLOW_UPS: <short follow-up question 1> | <short follow-up question 2> | <short follow-up question 3>""".replace("{{context}}", context or "- (no profile yet)")
            messages = [{"role": "system", "content": system}]
            for m in history[-12:]:
                text = (m.get("text") or m.get("content") or "").strip()
                if not text:
                    continue
                messages.append({"role": "user" if m.get("role") == "user" else "assistant", "content": text})
            messages.append({"role": "user", "content": query})
            reply = llm.chat(messages)
            if reply:
                suggestions: List[str] = []
                spoken = ""
                match = re.search(r"\n?\s*\**FOLLOW_UPS:?\**\s*(.+)\s*$", reply, re.IGNORECASE)
                if match:
                    suggestions = [x.strip(" -*") for x in match.group(1).split("|") if x.strip(" -*")][:3]
                    reply = reply[:match.start()].rstrip()
                match = re.search(r"\n?\s*\**SPOKEN:?\**\s*(.+)\s*$", reply, re.IGNORECASE)
                if match:
                    spoken = match.group(1).strip()
                    reply = reply[:match.start()].rstrip()
                if OUT_OF_SCOPE_REPLY[:40] in reply:
                    return AIService._out_of_scope()
                return {"response": reply, "spoken": spoken or _spoken_summary(reply),
                        "suggestions": suggestions or ["Can you explain that with an example?", "What should I practise next?", "How is this asked in interviews?"]}

        # Offline engine (no model configured or reachable)
        if not CareerKnowledgeEngine.is_in_scope(query):
            return AIService._out_of_scope()
        res = CareerKnowledgeEngine.get_response(query, history)
        res["spoken"] = _spoken_summary(res.get("response", ""))
        return res

    @staticmethod
    def _out_of_scope() -> Dict[str, Any]:
        return {
            "response": OUT_OF_SCOPE_REPLY + "\n\nYou can ask me about coding and DSA, CS and engineering topics, interviews, resumes, "
                        "your roadmap, communication skills, or how to use any GapX feature.",
            "spoken": OUT_OF_SCOPE_REPLY,
            "suggestions": ["How do I prepare for a technical interview?", "Explain hash maps simply", "How do I use the AI Roadmap?"],
        }

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
