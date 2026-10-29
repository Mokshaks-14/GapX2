"""Builds personalised roadmaps and topic notes from the curated roadmap data."""
import copy
import logging
from typing import Any, Dict, List, Optional

from app.services import llm
from app.services.interview_engine import detect_track
from app.services.interview_bank import TRACKS
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
        "interview_questions": [{"question": q, "ideal_answer": a, "difficulty": topic["difficulty"]} for q, a in topic["qa"]],
        "common_pitfalls": topic["pitfalls"],
        "resources": {
            "docs": [{"title": t, "url": u} for t, u in topic["docs"]],
            "videos": [{"title": q.title(), "url": youtube_link(q)} for q in topic["videos"]],
        },
        "summary": "Revise the last-minute notes the night before, then practise the interview question out loud.",
    }
    if llm.is_available():
        extra = llm.generate_json(f"""For the topic "{topic['title']}" (preparing for a {role} role), return STRICT JSON:
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
        data = llm.generate_json(f"""Write last-minute interview revision notes on "{topic_title}" (part of "{stage_title}") for a {role} candidate.
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
        "interview_questions": [{"question": q, "ideal_answer": a} for q, a in topic["qa"]],
        "resources": {"docs": [{"title": t, "url": u} for t, u in topic["docs"]],
                      "videos": [{"title": q.title(), "url": youtube_link(q)} for q in topic["videos"]]},
    }
