"""Builds personalised roadmaps and topic notes from the curated roadmap data."""
import copy
import logging
from typing import Any, Dict, List, Optional

from app.services import llm
from app.services.interview_engine import detect_track
from app.services.interview_bank import TRACKS
from app.services.notes import EXPLAINED
from app.services.roadmap_data import ROLE_ROADMAPS, youtube_link

logger = logging.getLogger(__name__)


def _topic_index() -> Dict[str, Dict[str, Any]]:
    index = {}
    for stages in ROLE_ROADMAPS.values():
        for stage in stages:
            for topic in stage["topics"]:
                index[topic["title"].lower()] = {"topic": topic, "stage": stage}
    return index


TOPIC_INDEX = _topic_index()


def _resources(topic: Dict[str, Any]) -> List[Dict[str, str]]:
    res = [{"type": "Documentation", "title": t, "url": u} for t, u in topic["docs"]]
    res += [{"type": "YouTube", "title": f"YouTube: {q}", "url": youtube_link(q)} for q in topic["videos"]]
    return res


def build_roadmap(role: str, skills: Optional[List[str]] = None) -> Dict[str, Any]:
    track = detect_track(role)
    known = {s.lower() for s in (skills or [])}
    stages = []
    for s_idx, stage in enumerate(ROLE_ROADMAPS[track], 1):
        topics = []
        for t_idx, topic in enumerate(stage["topics"], 1):
            title_l = topic["title"].lower()
            topics.append({
                "id": s_idx * 100 + t_idx,
                "title": topic["title"],
                "description": topic["description"],
                "estimated_hours": topic["estimated_hours"],
                "difficulty": topic["difficulty"],
                "concepts": [c.split(" — ")[0] for c in topic["concepts"]],
                "resources": _resources(topic),
                "already_familiar": any(k and len(k) > 2 and k in title_l for k in known),
                "is_completed": False,
            })
        stages.append({"id": s_idx, "title": stage["title"], "description": stage["description"], "topics": topics})
    return {"track": track, "track_label": TRACKS[track]["label"], "stages": stages}


def is_current_format(stages: List[Dict[str, Any]]) -> bool:
    return bool(stages) and all("concepts" in t for s in stages for t in s.get("topics", []))


def carry_over_progress(old_stages: List[Dict[str, Any]], new_stages: List[Dict[str, Any]]) -> None:
    done = {t.get("title", "").lower() for s in (old_stages or []) for t in s.get("topics", []) if t.get("is_completed")}
    for stage in new_stages:
        for topic in stage["topics"]:
            if topic["title"].lower() in done:
                topic["is_completed"] = True


def progress(stages: List[Dict[str, Any]]) -> float:
    topics = [t for s in stages for t in s.get("topics", [])]
    if not topics:
        return 0.0
    return round(100 * sum(1 for t in topics if t.get("is_completed")) / len(topics), 1)


def topic_notes(topic_title: str, stage_title: str, role: str) -> Dict[str, Any]:
    """Last-minute revision notes for one topic (curated content, optionally enriched by an LLM)."""
    entry = TOPIC_INDEX.get((topic_title or "").lower())
    if entry is None:
        return _generic_notes(topic_title, stage_title, role)
    topic = entry["topic"]
    concepts = []
    for c in topic["concepts"]:
        name, _, expl = c.partition(" — ")
        concepts.append({"name": name.strip(), "explanation": expl.strip() or name.strip()})
    notes = {
        "title": topic["title"],
        "stage": entry["stage"]["title"],
        "role": role,
        "executive_summary": f"{topic['description']} Estimated study time: about {topic['estimated_hours']} hours ({topic['difficulty']}).",
        "key_concepts": concepts,
        "last_minute_notes": topic["notes"],
        "explained": [{"point": p, "explanation": e} for p, e in EXPLAINED.get(topic["title"], {}).get("simple", [])],
        "interview_questions": [{"question": q, "ideal_answer": a, "difficulty": topic["difficulty"]}
                                for q, a in topic["qa"] + EXPLAINED.get(topic["title"], {}).get("qa", [])],
        "common_pitfalls": topic["pitfalls"],
        "resources": {
            "docs": [{"title": t, "url": u} for t, u in topic["docs"]],
            "videos": [{"title": q.title(), "url": youtube_link(q)} for q in topic["videos"]],
        },
        "summary": "Revise the last-minute notes the night before, then practise the interview question out loud.",
    }
    if llm.is_available():
        extra = llm.generate_json(fast=True, prompt=f"""For the topic "{topic['title']}" (preparing for a {role} role), return STRICT JSON:
{{"deep_dive": "a 120-180 word explanation of how it works under the hood, in plain language",
  "code_example": "a short, well-commented code example (or empty string if the topic isn't code-related)",
  "extra_questions": [{{"question": "...", "ideal_answer": "2-3 sentences"}}, {{"question": "...", "ideal_answer": "..."}}]}}""")
        if isinstance(extra, dict):
            if extra.get("deep_dive"):
                notes["internals_and_architecture"] = str(extra["deep_dive"])
            if extra.get("code_example"):
                notes["code_example"] = str(extra["code_example"])
            for qa in (extra.get("extra_questions") or [])[:2]:
                if isinstance(qa, dict) and qa.get("question"):
                    notes["interview_questions"].append({"question": str(qa["question"]), "ideal_answer": str(qa.get("ideal_answer", "")), "difficulty": "Medium"})
    return notes


def _generic_notes(topic_title: str, stage_title: str, role: str) -> Dict[str, Any]:
    data = None
    if llm.is_available():
        data = llm.generate_json(fast=True, prompt=f"""Write last-minute interview revision notes on "{topic_title}" (part of "{stage_title}") for a {role} candidate.
Return STRICT JSON: {{"executive_summary": "2-3 sentences", "key_concepts": [{{"name": "...", "explanation": "..."}}],
"last_minute_notes": ["5-7 crisp bullets"], "interview_questions": [{{"question": "...", "ideal_answer": "...", "difficulty": "Medium"}}],
"common_pitfalls": ["..."]}}""")
    notes = {
        "title": topic_title, "stage": stage_title, "role": role,
        "executive_summary": f"{topic_title} is part of {stage_title}. Regenerate your roadmap to get curated notes and video links for every topic.",
        "key_concepts": [], "last_minute_notes": [], "interview_questions": [], "common_pitfalls": [],
        "resources": {"docs": [], "videos": [{"title": f"{topic_title} explained", "url": youtube_link(f"{topic_title} explained")}]},
        "summary": "",
    }
    if isinstance(data, dict):
        for key in ("executive_summary", "key_concepts", "last_minute_notes", "interview_questions", "common_pitfalls"):
            if data.get(key):
                notes[key] = data[key]
    return notes


def all_notes(stages: List[Dict[str, Any]], role: str) -> List[Dict[str, Any]]:
    result = []
    for stage in stages:
        for topic in stage.get("topics", []):
            entry = TOPIC_INDEX.get(topic.get("title", "").lower())
            if entry:
                result.append(topic_notes_offline(entry, role))
    return result


def topic_notes_offline(entry: Dict[str, Any], role: str) -> Dict[str, Any]:
    """Curated notes only (no LLM call), used for the whole-roadmap cheat sheet."""
    topic = entry["topic"]
    return {
        "title": topic["title"], "stage": entry["stage"]["title"], "role": role,
        "key_concepts": [{"name": c.partition(" — ")[0], "explanation": c.partition(" — ")[2]} for c in topic["concepts"]],
        "last_minute_notes": topic["notes"],
        "explained": [{"point": p, "explanation": e} for p, e in EXPLAINED.get(topic["title"], {}).get("simple", [])],
        "interview_questions": [{"question": q, "ideal_answer": a} for q, a in topic["qa"] + EXPLAINED.get(topic["title"], {}).get("qa", [])],
        "resources": {"docs": [{"title": t, "url": u} for t, u in topic["docs"]],
                      "videos": [{"title": q.title(), "url": youtube_link(q)} for q in topic["videos"]]},
    }


# ─────────────────────────── personalised study plan ───────────────────────────
import re as _re
from datetime import date as _date, timedelta as _timedelta

_MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def _weeks_until(target: Optional[str], today: Optional[_date] = None) -> Optional[int]:
    """Understands 'June 2026', 'Within 6 Months', '3 months', '2026-06-01'."""
    if not target:
        return None
    today = today or _date.today()
    t = target.lower()
    m = _re.search(r"(\d+)\s*(month|week)", t)
    if m:
        n = int(m.group(1))
        return max(1, n * 4 if m.group(2) == "month" else n)
    m = _re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", t)
    if m:
        d = _date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return max(1, (d - today).days // 7)
    m = _re.search(r"([a-z]{3})[a-z]*\s+(\d{4})", t)
    if m and m.group(1) in _MONTHS:
        d = _date(int(m.group(2)), _MONTHS[m.group(1)], 1)
        return max(1, (d - today).days // 7)
    return None


def personalise(stages: List[Dict[str, Any]], user: Any) -> List[Dict[str, Any]]:
    """Adds personal notes to topics based on the user's skills, level and background."""
    level = (getattr(user, "experience_level", "") or "Beginner").lower()
    background = (getattr(user, "role", "") or "Student")
    for s_idx, stage in enumerate(stages):
        for topic in stage.get("topics", []):
            tips = []
            if topic.get("already_familiar"):
                tips.append("You listed this skill, so skim the notes and practise the interview questions.")
            if level in ("advanced", "intermediate") and topic.get("difficulty") == "Easy" and s_idx < 2:
                topic["optional"] = True
                tips.append("Foundational: review quickly at your level.")
            if background == "Career Switcher" and s_idx == 0:
                tips.append("Start here. Strong foundations make the switch much smoother.")
            if background == "Working Professional" and "System Design" in stage.get("title", ""):
                tips.append("Experienced candidates are tested heavily on this. Give it extra time.")
            topic["personal_tip"] = " ".join(tips) or None
    return stages


def study_plan(stages: List[Dict[str, Any]], hours_per_day: Optional[int], target: Optional[str]) -> Dict[str, Any]:
    """Splits the remaining topics into weeks (6 study days each), respecting the placement deadline."""
    hpd = max(1, min(12, int(hours_per_day or 2)))
    weekly = hpd * 6
    remaining = []
    for stage in stages:
        for topic in stage.get("topics", []):
            if topic.get("is_completed"):
                continue
            hours = topic.get("estimated_hours", 4)
            if topic.get("already_familiar") or topic.get("optional"):
                hours = max(1, round(hours / 2))
            remaining.append({"stage_id": stage["id"], "topic_id": topic["id"], "title": topic["title"],
                              "stage": stage["title"], "hours": hours})
    total = sum(t["hours"] for t in remaining)
    weeks_available = _weeks_until(target)

    weeks, current, used = [], [], 0
    for t in remaining:
        if current and used + t["hours"] > weekly:
            weeks.append({"topics": current, "hours": used})
            current, used = [], 0
        current.append(t)
        used += t["hours"]
    if current:
        weeks.append({"topics": current, "hours": used})
    start = _date.today()
    for i, w in enumerate(weeks):
        w["week"] = i + 1
        w["starts"] = (start + _timedelta(weeks=i)).strftime("%d %b")
        w["focus"] = w["topics"][0]["stage"]

    needed = len(weeks)
    summary = {"total_hours": total, "hours_per_day": hpd, "weeks_needed": needed, "weeks_available": weeks_available,
               "on_track": weeks_available is None or needed <= weeks_available}
    if weeks_available and needed > weeks_available:
        summary["recommended_hours_per_day"] = min(12, -(-total // (weeks_available * 6)))
        summary["message"] = (f"At {hpd} h/day you'll need about {needed} weeks, but your target is in {weeks_available}. "
                              f"Study about {summary['recommended_hours_per_day']} h/day, or skim the topics you already know.")
    elif needed == 0:
        summary["message"] = "Every topic is complete. Focus on mock interviews and coding practice now."
    else:
        summary["message"] = f"At {hpd} h/day you'll finish in about {needed} weeks" + \
            (f", comfortably before your target ({weeks_available} weeks away)." if weeks_available else ".")
    return {"summary": summary, "weeks": weeks}
