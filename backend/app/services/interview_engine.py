"""Adaptive mock-interview engine.

Runs a realistic interview flow (introduction → project deep-dive → role-specific technical
questions → scenario → behavioral → candidate's questions → wrap-up). Every next question is
chosen from what the candidate actually said:
  * technologies mentioned in the introduction drive the project deep-dive,
  * phrases in an answer trigger targeted follow-ups ("You mentioned useEffect…"),
  * partially correct answers get a probe for the concept they missed,
  * difficulty moves up or down with answer quality,
  * "can you repeat?", "what do you mean?", "I don't know" and "end interview" are handled naturally.

Works fully offline. When an LLM is configured it is used to grade answers more precisely and to
phrase the next question conversationally, while the engine keeps control of the interview flow.
"""
import json
import logging
import random
import re
from typing import Any, Dict, List, Optional, Tuple

from app.services import llm
from app.services.interview_bank import (BANK, BEHAVIORAL, CANDIDATE_QUESTION_REPLIES, SCENARIOS, TECH_LEXICON, TRACKS)

logger = logging.getLogger(__name__)

LEVELS = ["Easy", "Medium", "Hard"]
INTERVIEWER = "Alex"

REPEAT_RE = re.compile(r"\b(repeat( that| the question)?|say (that|it) again|pardon|didn'?t (hear|catch)|come again)\b", re.I)
CLARIFY_RE = re.compile(r"\b(what do you mean|clarify|rephrase|don'?t understand (the|your) question|can you explain the question|give me a hint|hint please)\b", re.I)
END_RE = re.compile(r"\b(conclude the interview|end (the|this) interview|stop (the|this) interview|leave the (call|interview)|end the call)\b", re.I)
DONT_KNOW_RE = re.compile(r"\b((i\s+)?(really\s+)?(don'?t|do not)\s+know|no idea|not sure|no clue|can'?t (recall|remember)|cannot answer|skip( this)?( question)?)\b", re.I)
NO_QUESTIONS_RE = re.compile(r"^\W*(no|nope|nothing|none|not really|i'?m good|that'?s all|no questions?)\b", re.I)
FILLER_RE = re.compile(r"\b(um+|uh+|erm|like|basically|actually|you know|i mean|sort of|kind of)\b", re.I)
HEDGE_RE = re.compile(r"\b(i think|maybe|probably|i guess|not sure|perhaps|might be)\b", re.I)
EXAMPLE_RE = re.compile(r"\b(for example|for instance|e\.g\.|such as|like when|in my project|we used|i used|because|so that)\b|\d", re.I)

DEEP_DIVE_KW = [
    ["the specific problem you hit", "problem", "issue", "challenge", "bug", "difficult", "hard", "struggl", "slow", "fail", "crash", "duplicate", "error", "broke"],
    ["how you solved it", "solved", "fixed", "implemented", "debug", "resolved", "figured", "approach", "added", "built", "introduced", "switched", "used", "rewrote", "optimi"],
    ["technical detail", "api", "database", "algorithm", "component", "model", "server", "query", "cache", "architecture", "framework", "library", "index", "constraint", "key", "endpoint", "state"] + TECH_LEXICON,
    ["the result or what you learned", "result", "improved", "reduced", "faster", "worked", "learned", "learnt", "outcome", "users", "%", "stopped", "saved", "increased"],
]
FOLLOWUP_KW = [
    ["a clear explanation", "because", "so that", "which means", "this allows", "the reason"],
    ["a concrete example", "for example", "for instance", "e.g.", "such as", "in my project", "we used", "i used"],
    ["trade-offs or edge cases", "trade-off", "tradeoff", "downside", "edge case", "however", "but", "instead", "drawback", "cost"],
]
INTRO_KW = [
    ["your background or education", "student", "degree", "b.tech", "btech", "engineering", "college", "university", "graduat", "year", "working", "experience", "currently", "startup", "company", "engineer", "developer"],
    ["a project or piece of work", "project", "built", "developed", "created", "worked on", "app", "website", "system", "internship", "service", "building", "api", "platform"],
    ["your skills", "python", "java", "javascript", "react", "sql", "skill", "machine learning", "c++", "programming", "language"],
    ["why this role", "interest", "passion", "enjoy", "excited", "want to", "goal", "love", "role", "proud", "looking for"],
]

ACK_GOOD = ["Good answer.", "That's a solid explanation.", "Nice, that covers the key points.", "Great, that's clear."]
ACK_OK = ["Okay, that's partly there.", "Fair enough, thanks.", "Alright.", "Thanks, I see where you're going."]
GENERIC_TERMS = {"resource", "state", "data", "memory", "value", "model", "table", "system", "server", "query", "index",
                 "example", "layer", "list", "array", "time", "result", "users", "project", "build", "code", "test", "function",
                 "error", "update", "write", "read", "slow", "fast", "change", "class", "object", "node", "tree", "file", "image"}
ACK_PROBE = ["Okay.", "Thanks.", "Got it.", "Alright."]
ACK_LOW = ["No problem.", "Okay, let's keep going.", "That's alright, let's move on."]


# ─── HELPERS ───────────────────────────────────────────────────────────────────
def detect_track(role: str, hint: Optional[str] = None) -> str:
    if hint and hint in TRACKS:
        return hint
    text = (role or "").lower()
    for track, meta in TRACKS.items():
        if track == "sde":
            continue
        if any(alias in text for alias in meta["aliases"]):
            return track
    return "sde"


def _lower(text: str) -> str:
    return f" {(text or '').lower()} "


def _has(text: str, phrase: str) -> bool:
    """Phrase match that respects word starts, so "post" doesn't match inside "postgresql"."""
    phrase = phrase.lower()
    if not phrase.strip():
        return False
    if not phrase[0].isalnum() or len(phrase.strip()) > 6:
        return phrase in text
    return re.search(r"(?<![a-z0-9])" + re.escape(phrase.strip()) + (r"(?![a-z0-9])" if len(phrase.strip()) <= 4 else ""), text) is not None


def coverage(answer: str, groups: List[List[str]]) -> Tuple[List[str], List[str]]:
    """Returns (covered concept names, missing concept names) for an answer."""
    text = _lower(answer)
    covered, missing = [], []
    for group in groups:
        name, synonyms = group[0], group[1:] or group
        (covered if any(_has(text, s) for s in synonyms) else missing).append(name)
    return covered, missing


def score_answer(answer: str, groups: List[List[str]]) -> Tuple[int, List[str], List[str]]:
    covered, missing = coverage(answer, groups)
    words = len(answer.split())
    cov = len(covered) / max(1, len(groups))
    depth = min(words / 60.0, 1.0)
    example = 1.0 if EXAMPLE_RE.search(answer or "") else 0.0
    score = round(100 * (0.68 * cov + 0.17 * depth + 0.15 * example))
    if words < 8:
        score = min(score, 30)
    elif words < 18:
        score = min(score, 60)
    return max(0, min(100, score)), covered, missing


def extract_tech(text: str) -> List[str]:
    """Technologies mentioned in the text, as whole words, most specific first, in order of mention."""
    lowered = _lower(text)
    hits = []
    for tech in TECH_LEXICON:
        t = tech.strip()
        m = re.search(r"(?<![a-z0-9+#.])" + re.escape(t) + r"(?![a-z0-9+#])", lowered)
        if m:
            hits.append((m.start(), t))
    names = [t for _, t in sorted(hits)]
    # drop names contained in a longer match (e.g. "sql" inside "postgresql", "react" inside "react native")
    return [t for t in dict.fromkeys(names) if not any(t != o and t in o for o in names)]


def _pretty_tech(t: str) -> str:
    special = {"next.js": "Next.js", "nextjs": "Next.js", "node": "Node.js", "fastapi": "FastAPI", "mongodb": "MongoDB", "postgresql": "PostgreSQL",
               "postgres": "PostgreSQL", "mysql": "MySQL", "sql": "SQL", "aws": "AWS", "gcp": "GCP", "llm": "LLMs", "rag": "RAG", "nlp": "NLP",
               "ios": "iOS", "css": "CSS", "html": "HTML", "rest api": "REST APIs", "c++": "C++", "javascript": "JavaScript", "typescript": "TypeScript",
               "pytorch": "PyTorch", "tensorflow": "TensorFlow", "scikit": "scikit-learn", "sklearn": "scikit-learn", "opencv": "OpenCV", "graphql": "GraphQL",
               "power bi": "Power BI", "github actions": "GitHub Actions", "iot": "IoT", "numpy": "NumPy", "openai": "the OpenAI API"}
    return special.get(t, t.title() if len(t) > 3 else t.upper())


def _pick(options: List[str], seed: int) -> str:
    return options[seed % len(options)]


def build_plan(interview_type: str, length: int) -> List[str]:
    t = (interview_type or "Mixed").lower()
    length = max(5, min(12, length or 8))
    if t in ("hr", "behavioral", "behavioural"):
        core = ["behavioral", "behavioral", "deep_dive", "behavioral", "behavioral", "behavioral", "behavioral", "behavioral", "behavioral"]
    elif t == "technical":
        core = ["deep_dive", "tech", "tech", "scenario", "tech", "tech", "tech", "tech", "scenario", "tech"]
    else:
        core = ["deep_dive", "tech", "tech", "scenario", "behavioral", "tech", "tech", "behavioral", "tech", "tech"]
    return ["intro"] + core[: length - 2] + ["closing"]


def _jd_terms(job_description: str) -> List[str]:
    return extract_tech(job_description or "")


# ─── ENGINE ────────────────────────────────────────────────────────────────────
class InterviewEngine:

    # ---------- start ----------
    @staticmethod
    def start(role: str, interview_type: str, experience_level: str, track_hint: Optional[str],
              job_description: Optional[str], candidate_name: Optional[str], length: int = 8,
              profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        track = detect_track(role, track_hint)
        is_fresher = (experience_level or "Fresher").lower() in ("fresher", "student", "entry level", "internship", "junior", "beginner")
        role_label = role.strip() if role and role.strip() else TRACKS[track]["label"]
        plan = build_plan(interview_type, length)
        state = {
            "track": track, "track_label": TRACKS[track]["label"], "role": role_label,
            "type": interview_type or "Mixed", "is_fresher": is_fresher,
            "jd_terms": _jd_terms(job_description or ""), "job_description": (job_description or "")[:1500],
            "plan": plan, "plan_idx": 0, "difficulty": "Easy" if is_fresher else "Medium",
            "asked_ids": [], "mentioned_tech": [], "followups_used": 0, "max_followups": max(3, len(plan) // 2),
            "probed_tech": [], "turns": [], "finished": False, "seed": random.randint(0, 10_000),
            "profile": profile or {},
            "profile_terms": extract_tech(" ".join((profile or {}).get("skills", []) + [(profile or {}).get("project_stack") or ""])),
        }
        first_name = (candidate_name or "").split(" ")[0] if candidate_name else ""
        greeting = f"Hi{(' ' + first_name) if first_name else ''}, I'm {INTERVIEWER}, your interviewer for the {role_label} role."
        prof = profile or {}
        if is_fresher:
            rest = "Please introduce yourself and tell me about a project you're proud of."
        else:
            rest = "Please walk me through your background and a recent project you're proud of."
        if prof.get("skills"):
            rest = f"I see you work with {', '.join(prof['skills'][:2])}. " + rest
        question = f"{greeting} {rest}"
        state["current"] = {"kind": "intro", "qid": None, "topic": "Introduction", "text": question, "is_followup": False}
        return {"state": state, "question": question, "difficulty": state["difficulty"], "phase": "Introduction",
                "total_questions": len(plan), "speech_parts": [greeting, rest]}

    # ---------- answer ----------
    @staticmethod
    def answer(state: Dict[str, Any], answer: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        answer = (answer or "").strip()
        cur = state["current"]

        # Conversational controls that don't consume a question
        if END_RE.search(answer):
            return InterviewEngine._finish(state, "Of course. Let's wrap up here. Thanks for your time today; your feedback report is ready.", ended_early=True)
        if cur["kind"] != "closing" and REPEAT_RE.search(answer) and len(answer.split()) < 12:
            return InterviewEngine._reply(state, f"Sure. {cur['text']}", feedback=None, repeat=True)
        if cur["kind"] not in ("closing", "intro") and CLARIFY_RE.search(answer) and len(answer.split()) < 16:
            hint = InterviewEngine._hint_for(cur)
            return InterviewEngine._reply(state, f"Let me put it another way. {hint} {cur['text']}", feedback=None, repeat=True)

        if cur["kind"] == "closing":
            return InterviewEngine._handle_closing(state, answer)

        record = InterviewEngine._evaluate(state, cur, answer, metrics)
        state["turns"].append(record)
        if cur.get("qid"):
            state["asked_ids"].append(cur["qid"])
        for tech in extract_tech(answer):
            if tech not in state["mentioned_tech"]:
                state["mentioned_tech"].append(tech)

        # Adapt difficulty on technical turns
        diff_change = "same"
        if cur["kind"] in ("tech", "scenario") or (cur["is_followup"] and cur.get("parent_kind") in ("tech", "scenario")):
            idx = LEVELS.index(state["difficulty"])
            if record["score"] >= 75 and idx < 2:
                state["difficulty"] = LEVELS[idx + 1]; diff_change = "increased"
            elif record["score"] < 40 and idx > 0:
                state["difficulty"] = LEVELS[idx - 1]; diff_change = "decreased"

        nxt = InterviewEngine._next_question(state, cur, answer, record)
        ack = InterviewEngine._acknowledge(state, record)
        if nxt is not None and nxt.get("is_followup") and record["score"] < 72 and not record["dont_know"]:
            ack = _pick(ACK_PROBE, state["seed"] + len(state["turns"]))

        # Let an LLM grade more precisely and phrase the next question naturally
        if llm.is_available():
            InterviewEngine._llm_enrich(state, cur, answer, record, nxt)
            # The spoken reaction stays a short stock phrase (its audio is cached, so it plays instantly)

        if nxt is None:
            return InterviewEngine._finish(state, f"{ack} That brings us to the end of the interview.")

        state["current"] = nxt
        question_part = f"{nxt.get('transition', '')} {nxt['text']}".replace("  ", " ").strip()
        spoken = f"{ack} {question_part}".strip()
        result = InterviewEngine._reply(state, spoken, feedback=record, diff_change=diff_change, next_text=nxt["text"])
        result["speech_parts"] = [ack, question_part]
        return result

    # ---------- evaluation ----------
    @staticmethod
    def _evaluate(state: Dict[str, Any], cur: Dict[str, Any], answer: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        kind = cur["kind"]
        q = InterviewEngine._question_by_id(cur.get("qid"))
        # Only a short "I don't know" counts as skipping; "not sure, but ..." followed by an attempt is a real answer
        dont_know = bool(DONT_KNOW_RE.search(answer)) and len(answer.split()) < 10

        if kind == "intro":
            groups = INTRO_KW
        elif cur["is_followup"] or kind == "deep_dive":
            groups = DEEP_DIVE_KW if kind == "deep_dive" else FOLLOWUP_KW
        else:
            groups = q["kw"] if q else FOLLOWUP_KW

        score, covered, missing = score_answer(answer, groups)
        if cur["is_followup"] and cur.get("probe_concept"):
            # A probe asks about one specific concept: judge mainly on whether they explained it
            mentioned = any(s in _lower(answer) for s in cur.get("probe_synonyms", []))
            score = max(score, 70) if mentioned and len(answer.split()) >= 12 else score
        if dont_know:
            score = min(score, 10)

        fillers = len(FILLER_RE.findall(answer))
        hedges = len(HEDGE_RE.findall(answer))
        words = len(answer.split())
        comm = 100
        if words < 15: comm -= 35
        elif words < 30: comm -= 15
        elif words > 260: comm -= 15
        comm -= min(30, fillers * 4)
        if EXAMPLE_RE.search(answer): comm += 5
        comm = max(20, min(100, comm))
        confidence = max(25, min(100, 90 - hedges * 8 - (25 if dont_know else 0) + (5 if words > 40 else 0)))

        if kind == "intro":
            fb = "Good introduction: it covered your background and a concrete project." if score >= 65 else \
                "A strong introduction is 60–90 seconds: education or role, two or three core skills, one project with its impact, and why this role."
        elif dont_know:
            fb = "It's fine to not know something. In a real interview, say what you do know and how you'd find the answer; that still earns credit."
        elif score >= 75:
            fb = f"Strong answer. You covered {', '.join(covered[:3])}."
        elif score >= 45:
            fb = f"Partly there. You covered {', '.join(covered[:2]) or 'the basics'}, but missed {', '.join(missing[:2])}."
        else:
            fb = f"This needs more depth. Key points to include: {', '.join(missing[:3])}."

        return {
            "kind": kind, "is_followup": cur["is_followup"], "qid": cur.get("qid"), "topic": cur.get("topic", ""),
            "question": cur["text"], "answer": answer, "score": score, "covered": covered, "missing": missing,
            "dont_know": dont_know, "communication": comm, "confidence": confidence, "fillers": fillers,
            "ideal": (q or {}).get("ideal") if not cur["is_followup"] and kind not in ("intro", "deep_dive") else cur.get("ideal"),
            "feedback": fb, "difficulty": state["difficulty"],
            "wpm": metrics.get("wpm"), "face": metrics.get("face"),
        }

    # ---------- choosing what comes next ----------
    @staticmethod
    def _next_question(state: Dict[str, Any], cur: Dict[str, Any], answer: str, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        seed = state["seed"] + len(state["turns"])
        plan_left = len(state["plan"]) - state["plan_idx"] - 1
        can_follow = (not cur["is_followup"]) and state["followups_used"] < state["max_followups"] and plan_left >= 1 and not record["dont_know"]

        # 0) Any technology the candidate brings up gets probed, like a real interviewer would
        if can_follow and cur["kind"] in ("deep_dive", "tech") and record["score"] >= 40:
            probed = set(state.setdefault("probed_tech", []))
            q = InterviewEngine._question_by_id(cur.get("qid"))
            fu_triggers = {t for trig, _ in (q or {}).get("fu", []) for t in trig}
            new_tech = [t for t in extract_tech(answer) if t not in probed and t not in fu_triggers and t not in ("html", "css", "excel")]
            if new_tech and (cur["kind"] == "deep_dive" or len(new_tech) and not any(t in _lower(answer) for t in fu_triggers)):
                tech = new_tech[0]
                state["probed_tech"].append(tech)
                state["followups_used"] += 1
                pretty = _pretty_tech(tech)
                text = _pick([
                    f"You mentioned {pretty}. Why did you choose {pretty} there, and what limitations or trade-offs did you run into?",
                    f"How does {pretty} work under the hood in what you built?",
                    f"Let's stay on {pretty} for a moment. What's one problem you hit with it, and how did you debug it?",
                ], seed)
                return {"kind": cur["kind"], "parent_kind": cur["kind"], "qid": None, "topic": f"{pretty} (from your answer)",
                        "is_followup": True, "text": text, "transition": "", "ideal": None}
        if can_follow and cur["kind"] == "deep_dive" and record["score"] < 65:
            state["followups_used"] += 1
            missing = record["missing"][0] if record["missing"] else "the result"
            return {"kind": "deep_dive", "parent_kind": "deep_dive", "qid": None, "topic": "Project Deep-Dive", "is_followup": True,
                    "text": f"Tell me more about {missing}. How did you test that it worked?",
                    "transition": "", "ideal": None}

        # 1) Follow-ups on main technical / behavioral questions
        if can_follow and cur["kind"] in ("tech", "scenario", "behavioral"):
            q = InterviewEngine._question_by_id(cur.get("qid"))
            lowered = _lower(answer)
            if q and record["score"] >= 45:
                for triggers, fu_text in q.get("fu", []):
                    hit = next((t for t in triggers if t in lowered), None)
                    if hit:
                        state["followups_used"] += 1
                        return {"kind": cur["kind"], "parent_kind": cur["kind"], "qid": None, "topic": cur.get("topic"), "is_followup": True,
                                "text": fu_text, "transition": "", "ideal": None}
            if q and 35 <= record["score"] < 72 and record["missing"]:
                concept = record["missing"][0]
                synonyms = next((g[1:] or g for g in q["kw"] if g[0] == concept), [])
                state["followups_used"] += 1
                if cur["kind"] == "behavioral":
                    text = f"Could you tell me more about {concept} in that example?"
                else:
                    text = f"You didn't mention {concept}. How does that fit into your answer?"
                return {"kind": cur["kind"], "parent_kind": cur["kind"], "qid": None, "topic": cur.get("topic"), "is_followup": True,
                        "text": text, "transition": "", "probe_concept": concept, "probe_synonyms": synonyms, "ideal": q.get("ideal")}

        # 2) Move to the next planned phase
        state["plan_idx"] += 1
        if state["plan_idx"] >= len(state["plan"]):
            return None
        kind = state["plan"][state["plan_idx"]]

        if kind == "closing":
            return {"kind": "closing", "qid": None, "topic": "Your questions", "is_followup": False, "transition": "",
                    "text": "That's all from my side. Do you have any questions for me?"}

        if kind == "deep_dive":
            return InterviewEngine._deep_dive_question(state, seed)

        q = InterviewEngine._select_question(state, kind, seed)
        if q is None:  # bank exhausted: fall back to a technical question or end
            q = InterviewEngine._select_question(state, "tech", seed)
            if q is None:
                return None
        link = state.pop("_last_link", None)
        if link and kind == "tech":
            transition = _pick([f"Building on {link}:", f"Since you mentioned {link}:", f"Following up on {link}:"], seed)
            return {"kind": kind, "qid": q["id"], "topic": q["topic"], "is_followup": False, "text": q["q"], "transition": transition}
        project = (state.get("profile") or {}).get("project_title")
        if kind == "behavioral" and q["id"] in ("bh-1", "bh-2", "bh-5") and (project or any(t["kind"] == "deep_dive" for t in state["turns"])):
            ref = f"the {project} project" if project else "the project you described earlier"
            return {"kind": kind, "qid": q["id"], "topic": q["topic"], "is_followup": False,
                    "text": q["q"] + f" You can use {ref}.",
                    "transition": "Now a behavioral question."}
        transition = {
            "tech": _pick([f"Next, {q['topic']}.", f"Now, {q['topic']}.", f"On {q['topic']}:"], seed),
            "scenario": "",  # scenario questions introduce themselves
            "behavioral": _pick(["Now a behavioral question.", "About how you work:", "A question on teamwork:"], seed),
        }.get(kind, "")
        return {"kind": kind, "qid": q["id"], "topic": q["topic"], "is_followup": False, "text": q["q"], "transition": transition}

    @staticmethod
    def _deep_dive_question(state: Dict[str, Any], seed: int) -> Dict[str, Any]:
        intro = next((t["answer"] for t in state["turns"] if t["kind"] == "intro"), "")
        techs = [t for t in state["mentioned_tech"] if t not in ("html", "css", "excel")]
        prof = state.get("profile") or {}
        title, stack = prof.get("project_title"), prof.get("project_stack")
        if title:
            built = f", built with {stack}" if stack else ""
            text = f"Tell me about your project {title}{built}: what you built and the hardest challenge you faced."
        elif len(intro.split()) < 12:
            text = "Pick one project you've built: what does it do, what was your part, and which tech did you use?"
        elif techs:
            tech = _pretty_tech(techs[0])
            text = f"You mentioned {tech}. What was the hardest problem you hit with {tech}, and how did you solve it?"
        elif re.search(r"\bproject|built|developed|created\b", intro, re.I):
            text = "Let's go deeper: what was the architecture, which part did you build, and what would you change today?"
        else:
            text = "Tell me about a project you've built: the problem it solved, your part, and the hardest bit."
        if not state["is_fresher"] and techs and len(text.split()) < 20:
            text += " What was the impact?"
        return {"kind": "deep_dive", "qid": None, "topic": "Project Deep-Dive", "is_followup": False, "text": text,
                "transition": "", "ideal": "A strong project answer names the specific problem, the options you considered, what YOU built, the technology involved, and a measurable result or lesson."}

    @staticmethod
    def _select_question(state: Dict[str, Any], kind: str, seed: int) -> Optional[Dict[str, Any]]:
        asked = set(state["asked_ids"])
        if kind == "behavioral":
            pool = [q for q in BEHAVIORAL if q["id"] not in asked]
            if state["type"].lower() not in ("hr", "behavioral"):
                pool = [q for q in pool if q["id"] != "bh-7"] or pool
            if not pool:
                return None
            # Ask motivation near the end of HR rounds
            if state["type"].lower() in ("hr", "behavioral") and state["plan_idx"] >= len(state["plan"]) - 2:
                motivation = next((q for q in pool if q["id"] == "bh-7"), None)
                if motivation:
                    return motivation
            return pool[seed % len(pool)]

        if kind == "scenario":
            pool = [q for q in SCENARIOS.get(state["track"], []) if q["id"] not in asked]
            if not pool:
                pool = [q for q in SCENARIOS["sde"] if q["id"] not in asked]
            return pool[seed % len(pool)] if pool else None

        pool = [q for q in BANK.get(state["track"], []) if q["id"] not in asked]
        if not pool:
            pool = [q for q in BANK["sde"] if q["id"] not in asked]
        if not pool:
            return None
        target = state["difficulty"]
        if state["is_fresher"] and target == "Hard" and len([t for t in state["turns"] if t["kind"] == "tech"]) < 2:
            target = "Medium"
        interests = set(state["jd_terms"]) | set(state["mentioned_tech"]) | set(state.get("profile_terms", []))

        # What the candidate just talked about (most recent answer counts double)
        recent = [t["answer"] for t in state["turns"][-2:]]
        weights = [1, 2][-len(recent):] if recent else []
        recent_text = [(_lower(a), w) for a, w in zip(recent, weights)]

        def relation(q: Dict[str, Any]) -> Tuple[int, Optional[str]]:
            score, best = 0, None
            for group in q["kw"]:
                for syn in group[1:] or group:
                    syn_l = syn.lower().strip()
                    if len(syn_l) < 4 or syn_l in GENERIC_TERMS:
                        continue
                    for text, w in recent_text:
                        if _has(text, syn_l):
                            score += w
                            best = best or syn_l
                            break
                    else:
                        continue
                    break
            return score, best

        def rank(q: Dict[str, Any]) -> float:
            text = (q["q"] + " " + " ".join(s for g in q["kw"] for s in g)).lower()
            rel, _ = relation(q)
            interest = sum(1 for t in interests if t in text)
            level_gap = abs(LEVELS.index(q["level"]) - LEVELS.index(target))
            custom = 6 if q.get("custom") else 0   # questions added in the admin panel come first
            return rel * 3 + interest - level_gap * 2.5 + custom + ((hash(q["id"]) + seed) % 97) / 1000

        best = max(pool, key=rank)
        rel, term = relation(best)
        if rel >= 2 and term:
            state["_last_link"] = _pretty_tech(term) if term in TECH_LEXICON else term
        return best

    # ---------- closing ----------
    @staticmethod
    def _handle_closing(state: Dict[str, Any], answer: str) -> Dict[str, Any]:
        state["turns"].append({"kind": "closing", "is_followup": False, "qid": None, "topic": "Your questions",
                               "question": state["current"]["text"], "answer": answer, "score": None})
        if NO_QUESTIONS_RE.search(answer) or len(answer.split()) < 3:
            reply = "No problem at all."
        else:
            lowered = answer.lower()
            reply = next((r for keys, r in CANDIDATE_QUESTION_REPLIES if any(k in lowered for k in keys)),
                         "That's a thoughtful question. The team would be happy to go deeper on it in the next round.")
            reply += " Asking questions like that shows real interest, so it's a good habit."
        return InterviewEngine._finish(state, f"{reply} Thank you for your time today. That concludes the interview, and your detailed feedback report is ready.")

    # ---------- responses ----------
    @staticmethod
    def _acknowledge(state: Dict[str, Any], record: Dict[str, Any]) -> str:
        seed = state["seed"] + len(state["turns"])
        if record["dont_know"]:
            return "That's okay, it's better to say so than to guess."
        if record["kind"] == "intro":
            return "Thanks for the introduction."
        if record["score"] >= 72:
            return _pick(ACK_GOOD, seed)
        if record["score"] >= 45:
            return _pick(ACK_OK, seed)
        return _pick(ACK_LOW, seed)

    @staticmethod
    def _reply(state: Dict[str, Any], spoken: str, feedback: Optional[Dict[str, Any]], repeat: bool = False,
               diff_change: str = "same", next_text: Optional[str] = None) -> Dict[str, Any]:
        scored = [t["score"] for t in state["turns"] if t.get("score") is not None]
        live = round(sum(scored) / len(scored)) if scored else None
        conf = [t["confidence"] for t in state["turns"] if t.get("confidence") is not None]
        cur = state["current"]
        main_number = min(state["plan_idx"] + 1, len(state["plan"]))
        return {
            "next_question": next_text or cur["text"],
            "is_finished": False,
            "is_repeat": repeat,
            "ai_immediate_feedback": feedback["feedback"] if feedback else None,
            "is_correct": (feedback["score"] >= 60) if feedback and feedback.get("score") is not None else True,
            "ai_correction": (f"Missing: {', '.join(feedback['missing'][:3])}." if feedback and feedback.get("missing") and feedback["score"] < 75 else None),
            "ideal_answer": feedback.get("ideal") if feedback else None,
            "speech_text_to_speak": spoken,
            "current_live_score": live,
            "confidence_metric": round(sum(conf) / len(conf)) if conf else None,
            "difficulty": state["difficulty"],
            "difficulty_change": diff_change,
            "phase": cur.get("topic") or cur["kind"].title(),
            "question_kind": "follow-up" if cur.get("is_followup") else cur["kind"],
            "question_number": main_number,
            "total_questions": len(state["plan"]),
            "turn_score": feedback.get("score") if feedback else None,
        }

    @staticmethod
    def _finish(state: Dict[str, Any], spoken: str, ended_early: bool = False) -> Dict[str, Any]:
        state["finished"] = True
        state["ended_early"] = ended_early
        last = state["turns"][-1] if state["turns"] else None
        result = InterviewEngine._reply(state, spoken, feedback=last if last and last.get("score") is not None else None)
        result.update({"is_finished": True, "next_question": None, "speech_text_to_speak": spoken, "question_kind": "end"})
        return result

    # ---------- final report ----------
    @staticmethod
    def report(state: Dict[str, Any], behavior: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        turns = [t for t in state["turns"] if t.get("score") is not None]
        if not turns:
            empty = {"technical_score": 0, "communication_score": 0, "confidence_score": 0, "problem_solving_score": 0,
                     "leadership_score": 0, "overall_score": 0}
            empty["feedback"] = {
                "strengths": [], "weaknesses": ["The interview ended before any questions were answered."], "mistakes": [],
                "ideal_answers": [], "suggestions": ["Start a new session and answer at least a few questions to get a scored report."],
                "practice_plan": [], "turns": [],
            }
            return empty

        def avg(values: List[float], default: Optional[float] = None) -> Optional[int]:
            values = [v for v in values if v is not None]
            return round(sum(values) / len(values)) if values else default

        tech_turns = [t for t in turns if t["kind"] in ("tech", "scenario")]
        technical = avg([t["score"] for t in tech_turns])
        problem = avg([t["score"] for t in turns if t["kind"] in ("scenario", "deep_dive")] +
                      [t["score"] for t in tech_turns if t.get("difficulty") == "Hard"])
        behavioral = avg([t["score"] for t in turns if t["kind"] == "behavioral"])
        communication = avg([t["communication"] for t in turns], 60)
        confidence = avg([t["confidence"] for t in turns], 60)
        if behavior and behavior.get("has_face_data"):
            confidence = round(0.6 * confidence + 0.4 * behavior.get("avg_confidence", confidence))
        overall_all = avg([t["score"] for t in turns], 0)

        technical = technical if technical is not None else overall_all
        problem = problem if problem is not None else technical
        leadership = behavioral if behavioral is not None else communication
        if state["type"].lower() in ("hr", "behavioral"):
            overall = round(0.45 * leadership + 0.25 * communication + 0.15 * confidence + 0.15 * problem)
        else:
            overall = round(0.4 * technical + 0.2 * problem + 0.15 * communication + 0.1 * confidence + 0.15 * leadership)

        # Topic-level strengths and gaps
        strong = [t for t in turns if t["score"] >= 72 and t["kind"] != "intro"]
        weak = sorted([t for t in turns if t["score"] < 55], key=lambda t: t["score"])
        strengths = []
        for t in strong[:4]:
            strengths.append(f"{t['topic']}: covered {', '.join(t['covered'][:3]) or 'the key ideas'} clearly.")
        if communication >= 75:
            strengths.append("Clear, well-paced communication with few filler words.")
        if any(t["kind"] == "intro" and t["score"] >= 65 for t in turns):
            strengths.append("Confident, well-structured self-introduction.")

        weaknesses, mistakes, ideal_answers = [], [], []
        for t in weak[:4]:
            gap = ", ".join(t["missing"][:3]) or "depth and concrete examples"
            weaknesses.append(f"{t['topic']}: missing {gap}.")
            short_q = t["question"] if len(t["question"]) < 140 else t["question"][:137] + "..."
            mistakes.append(f"\"{short_q}\": " + ("you skipped this one." if t["dont_know"] else f"your answer didn't cover {gap}."))
            if t.get("ideal"):
                ideal_answers.append({"question": t["question"], "ideal_answer": t["ideal"]})

        fillers = sum(t.get("fillers", 0) for t in turns)
        avg_words = avg([len(t["answer"].split()) for t in turns], 0)
        suggestions = []
        if avg_words < 35:
            suggestions.append("Your answers were short. Aim for 45–120 seconds: define the concept, explain how it works, give an example, then mention a trade-off.")
        if fillers >= 5:
            suggestions.append(f"You used about {fillers} filler words ('um', 'like', 'basically'). Pause silently instead; it sounds more confident.")
        if behavioral is not None and behavioral < 65:
            suggestions.append("Structure behavioral answers with STAR (Situation, Task, Action, Result), and end with a measurable result.")
        if technical < 65:
            suggestions.append("For technical questions, state the definition first, then the mechanism, then a real example from your projects.")
        if not any(EXAMPLE_RE.search(t["answer"]) for t in turns):
            suggestions.append("Back up claims with concrete examples from your own projects; interviewers remember specifics.")
        if state.get("ended_early"):
            suggestions.append("You ended the interview early. Completing the full round gives a more reliable score.")
        if not suggestions:
            suggestions.append("Keep it up: try the Hard difficulty track or a different interview format next.")

        weak_topics = [t["topic"] for t in weak][:3]
        practice_plan = []
        if weak_topics:
            practice_plan.append(f"Days 1–2: Revise {', '.join(weak_topics)} using the matching stages in your GapX roadmap and their last-minute notes.")
        practice_plan.append("Days 3–4: Write out model answers for the questions you found hardest and say them aloud, timing yourself at about 90 seconds.")
        if state["type"].lower() != "hr":
            practice_plan.append("Days 5–6: Solve 4–5 coding problems in the Coding Practice module and explain your approach out loud while coding.")
        practice_plan.append("Day 7: Take another mock interview in the same field and compare your scores.")

        return {
            "technical_score": technical, "communication_score": communication, "confidence_score": confidence,
            "problem_solving_score": problem, "leadership_score": leadership, "overall_score": overall,
            "feedback": {
                "strengths": strengths or ["You completed the interview; keep practising to build depth."],
                "weaknesses": weaknesses, "mistakes": mistakes, "ideal_answers": ideal_answers,
                "suggestions": suggestions, "practice_plan": practice_plan,
                "turns": [{"topic": t["topic"], "question": t["question"], "answer": t["answer"], "score": t["score"],
                           "covered": t["covered"], "missing": t["missing"], "is_followup": t["is_followup"]} for t in turns],
                "track": state["track_label"],
            },
        }

    # ---------- utilities ----------
    @staticmethod
    def _question_by_id(qid: Optional[str]) -> Optional[Dict[str, Any]]:
        if not qid:
            return None
        for bank in list(BANK.values()) + list(SCENARIOS.values()) + [BEHAVIORAL]:
            for q in bank:
                if q["id"] == qid:
                    return q
        return None

    @staticmethod
    def _hint_for(cur: Dict[str, Any]) -> str:
        q = InterviewEngine._question_by_id(cur.get("qid"))
        if q and q.get("hint"):
            return f"Hint: {q['hint']}"
        if cur.get("probe_concept"):
            return f"I'm asking specifically about {cur['probe_concept']}: what it is and why it matters here."
        return "Just walk me through your thinking step by step, using an example if it helps."

    @staticmethod
    def _llm_enrich(state: Dict[str, Any], cur: Dict[str, Any], answer: str, record: Dict[str, Any], nxt: Optional[Dict[str, Any]]) -> None:
        """Uses an LLM to grade the answer and rephrase the next question so it references the candidate's words."""
        recent = state["turns"][-4:]
        convo = "\n".join(f"Q: {t['question']}\nA: {t['answer']}" for t in recent)
        next_intent = "end the interview" if nxt is None else nxt["text"]
        prompt = f"""You are {INTERVIEWER}, a friendly but rigorous interviewer for a {state['role']} ({state['track_label']}) position.
Candidate level: {'fresher / student' if state['is_fresher'] else 'experienced'}.
{('Job description keywords: ' + ', '.join(state['jd_terms'])) if state['jd_terms'] else ''}
Recent conversation:
{convo}

The candidate just answered: "{answer}"
To the question: "{cur['text']}"
Concepts a strong answer covers: {', '.join(c for c in (record['covered'] + record['missing'])) or 'clarity, depth, examples'}.

The NEXT thing you will ask: "{next_intent}"
Rephrase it in at most 25 words (one or two short sentences) so it builds on something specific the candidate just said, e.g. "You mentioned X; ...".
Keep the same topic and difficulty. Don't repeat their whole answer back.

Return STRICT JSON:
{{"score": 0-100 (how good the answer is for this level),
  "acknowledgement": "one short natural sentence reacting to their specific answer (no praise if it was weak)",
  "feedback": "1-2 sentences of coaching on this answer",
  "missing": ["key concepts they missed"],
  "ideal_answer": "a crisp model answer in 2-3 sentences",
  "next_question": "the next question as you'd say it"}}"""
        data = llm.generate_json(prompt, fast=True)
        if not isinstance(data, dict):
            return
        try:
            llm_score = int(data.get("score"))
            record["score"] = round(0.5 * record["score"] + 0.5 * max(0, min(100, llm_score)))
        except (TypeError, ValueError):
            pass
        if data.get("feedback"):
            record["feedback"] = str(data["feedback"])
        if isinstance(data.get("missing"), list):
            record["missing"] = [str(m) for m in data["missing"]][:4]
        if data.get("ideal_answer") and cur["kind"] not in ("intro",):
            record["ideal"] = str(data["ideal_answer"])
        if data.get("acknowledgement"):
            record["llm_ack"] = str(data["acknowledgement"])
        rephrased = str(data.get("next_question") or "").strip()
        if nxt is not None and rephrased and nxt["kind"] != "closing" and len(rephrased.split()) <= 32:
            nxt["text"] = rephrased  # only accepted when it still fits in about two lines
            nxt["transition"] = ""
