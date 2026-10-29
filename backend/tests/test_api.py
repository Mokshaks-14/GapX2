from datetime import datetime, timedelta

from jose import jwt

from tests.conftest import register

API = "/api/v1"


# ─── Auth & security ─────────────────────────────────────────────
def test_requests_without_token_are_rejected(client):
    assert client.get(f"{API}/users/me").status_code == 401


def test_garbage_and_legacy_tokens_are_rejected(client, make_user):
    make_user()  # make sure users exist, so the old "fall back to first user" path would have triggered
    for token in ("garbage", "null", "local_123", "demo_abc", "guest_x"):
        r = client.get(f"{API}/users/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401, token


def test_expired_token_is_rejected(client, make_user):
    from app.core.config import settings
    headers = make_user()
    me = client.get(f"{API}/users/me", headers=headers).json()
    expired = jwt.encode({"sub": str(me["id"]), "exp": datetime.utcnow() - timedelta(minutes=1)}, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    assert client.get(f"{API}/users/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_login_works_and_wrong_password_fails(client):
    register(client, "Login.Case@gapx.test", password="Correct123")
    assert client.post(f"{API}/auth/login", json={"email": "login.case@gapx.test", "password": "Correct123"}).status_code == 200
    assert client.post(f"{API}/auth/login", json={"email": "login.case@gapx.test", "password": "nope"}).status_code == 400


def test_admin_prefix_no_longer_grants_admin(client):
    headers = register(client, "admin.hacker@gapx.test")
    assert client.get(f"{API}/users/me", headers=headers).json()["is_admin"] is False
    assert client.get(f"{API}/admin/metrics", headers=headers).status_code == 403


def test_configured_admin_email_is_admin(client):
    headers = register(client, "boss@gapx.test")
    assert client.get(f"{API}/users/me", headers=headers).json()["is_admin"] is True
    assert client.get(f"{API}/admin/metrics", headers=headers).status_code == 200


def test_google_login_requires_real_credential(client):
    cfg = client.get(f"{API}/auth/config").json()
    assert cfg["google_client_id"] is None
    # The old endpoint accepted any email; now an unverifiable credential is refused
    r = client.post(f"{API}/auth/google", json={"credential": "fake-token"})
    assert r.status_code in (400, 401, 501)
    assert client.post(f"{API}/auth/google", json={"email": "victim@gapx.test"}).status_code == 422


def test_demo_login(client):
    r = client.post(f"{API}/auth/demo")
    assert r.status_code == 200
    me = client.get(f"{API}/users/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"}).json()
    assert me["email"] == "demo@gapx.ai"


def test_notes_pdf_requires_auth(client):
    assert client.get(f"{API}/roadmaps/notes-pdf/1/101").status_code == 401


# ─── Onboarding, roadmap & XP ────────────────────────────────────
def onboard(client, headers, role="Frontend Engineer"):
    r = client.post(f"{API}/users/onboard", headers=headers, json={
        "role": "Student", "skills": ["React"], "languages_known": ["JavaScript"], "target_roles": [role],
        "degree_branch": "B.Tech CSE", "college_name": "Test University"})
    assert r.status_code == 200, r.text
    return r.json()


def test_roadmap_is_role_specific_with_resources(client, make_user):
    headers = make_user()
    onboard(client, headers, "Data Scientist")
    rm = client.post(f"{API}/roadmaps/generate", headers=headers).json()
    titles = [s["title"] for s in rm["stages_data"]]
    assert "Statistics & Probability" in titles
    topic = rm["stages_data"][0]["topics"][0]
    assert topic["concepts"] and any(r["type"] == "YouTube" for r in topic["resources"])
    notes = client.get(f"{API}/roadmaps/notes/1/{topic['id']}", headers=headers).json()
    assert notes["last_minute_notes"] and notes["resources"]["videos"]
    pdf = client.get(f"{API}/roadmaps/notes-pdf/1/{topic['id']}", headers=headers)
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
    sheet = client.get(f"{API}/roadmaps/cheatsheet-pdf", headers=headers)
    assert sheet.status_code == 200 and sheet.content[:4] == b"%PDF"


def test_regenerating_roadmap_does_not_farm_xp_and_keeps_progress(client, make_user):
    headers = make_user()
    onboard(client, headers)
    rm = client.post(f"{API}/roadmaps/generate", headers=headers).json()
    first = rm["stages_data"][0]["topics"][0]
    client.post(f"{API}/roadmaps/toggle-topic", headers=headers, json={"stage_id": 1, "topic_id": first["id"], "is_completed": True})
    xp = client.get(f"{API}/users/me", headers=headers).json()["xp"]
    for _ in range(3):
        rm = client.post(f"{API}/roadmaps/generate", headers=headers).json()
    assert client.get(f"{API}/users/me", headers=headers).json()["xp"] == xp
    assert rm["stages_data"][0]["topics"][0]["is_completed"] is True
    # Toggling an already-completed topic again must not add XP
    client.post(f"{API}/roadmaps/toggle-topic", headers=headers, json={"stage_id": 1, "topic_id": first["id"], "is_completed": True})
    assert client.get(f"{API}/users/me", headers=headers).json()["xp"] == xp


# ─── Interview ───────────────────────────────────────────────────
def test_interview_flow_is_dynamic_and_role_based(client, make_user):
    headers = make_user(name="Asha Rao")
    start = client.post(f"{API}/interviews/start", headers=headers, json={
        "target_role": "Frontend Engineer", "experience_level": "Fresher", "interview_type": "Mixed", "num_questions": 6}).json()
    assert start["track"] == "frontend" and "Asha" in start["first_question"]
    iid = start["interview_id"]

    r = client.post(f"{API}/interviews/{iid}/answer", headers=headers, json={
        "answer": "I'm a final year computer science student. I built a recipe website with React and Firebase and I enjoy UI work."}).json()
    assert r["question_kind"] == "deep_dive" and "React" in r["next_question"]

    r = client.post(f"{API}/interviews/{iid}/answer", headers=headers, json={"answer": "Could you repeat that?"}).json()
    assert r["is_repeat"] is True

    answers = [
        "The feed re-rendered too often so I profiled it, split the context and used React.memo which made scrolling smooth.",
        "var is function scoped, let and const are block scoped, const can't be reassigned, and hoisting with the temporal dead zone.",
        "I don't know",
        "debounce the input and abort stale requests with AbortController, cache results and show a loading state.",
        "What does a typical day look like?",
        "No more questions.",
        "Thanks!",
    ]
    for a in answers:
        r = client.post(f"{API}/interviews/{iid}/answer", headers=headers, json={"answer": a}).json()
        if r["is_finished"]:
            break
    assert r["is_finished"] is True

    fb = client.get(f"{API}/interviews/{iid}/feedback", headers=headers).json()
    assert 0 <= fb["overall_score"] <= 100
    assert fb["feedback"]["turns"] and "engine" not in fb["feedback"]
    assert client.post(f"{API}/interviews/{iid}/answer", headers=headers, json={"answer": "more"}).status_code == 409


def test_interview_ended_immediately_gives_zero_not_fake_score(client, make_user):
    headers = make_user()
    iid = client.post(f"{API}/interviews/start", headers=headers, json={
        "target_role": "Backend Engineer", "experience_level": "Experienced", "interview_type": "Technical"}).json()["interview_id"]
    r = client.post(f"{API}/interviews/{iid}/answer", headers=headers, json={"answer": "Thank you, I would like to conclude the interview."}).json()
    assert r["is_finished"] is True
    fb = client.get(f"{API}/interviews/{iid}/feedback", headers=headers).json()
    assert fb["overall_score"] == 0


def test_other_users_interview_is_not_accessible(client, make_user):
    a, b = make_user(), make_user()
    iid = client.post(f"{API}/interviews/start", headers=a, json={
        "target_role": "SDE", "experience_level": "Fresher", "interview_type": "Mixed"}).json()["interview_id"]
    assert client.post(f"{API}/interviews/{iid}/answer", headers=b, json={"answer": "hi"}).status_code == 404


# ─── Resume ──────────────────────────────────────────────────────
RESUME = {
    "name": "Asha Rao", "headline": "Frontend Engineer", "email": "asha@example.com",
    "linkedin": "https://linkedin.com/in/asha", "github": "https://github.com/asha",
    "education": "B.Tech CSE", "college": "Test University", "cgpa": "8.7",
    "skills": ["React", "TypeScript"], "languages": ["JavaScript"], "frameworks": ["Next.js"], "tools": ["Git"],
    "projects": [{"name": "Recipe Hub", "stack": "React, Firebase", "bullets": ["Built an app used by 300 students"]}],
    "interests": ["Open source", "Chess"],
}


def test_resume_summary_pdf_and_single_xp_award(client, make_user):
    headers = make_user()
    summary = client.post(f"{API}/resumes/generate-summary", headers=headers, json=RESUME).json()["summary"]
    assert "Frontend Engineer" in summary and len(summary) > 40

    pdf = client.post(f"{API}/resumes/download-pdf", headers=headers, json={**RESUME, "summary": summary})
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
    assert b"/MediaBox [ 0 0 595.2756 841.8898 ]" in pdf.content  # A4

    client.post(f"{API}/resumes/manual", headers=headers, json=RESUME)
    xp_after_first = client.get(f"{API}/users/me", headers=headers).json()["xp"]
    client.post(f"{API}/resumes/manual", headers=headers, json=RESUME)
    assert client.get(f"{API}/users/me", headers=headers).json()["xp"] == xp_after_first


def test_invalid_linkedin_is_rejected(client, make_user):
    headers = make_user()
    r = client.post(f"{API}/resumes/manual", headers=headers, json={**RESUME, "linkedin": "https://evil.com/in/x"})
    assert r.status_code == 400


# ─── Coding ──────────────────────────────────────────────────────
def test_problem_details_hide_hidden_tests(client, make_user):
    headers = make_user()
    problems = client.get(f"{API}/coding/problems", headers=headers).json()
    assert len(problems) >= 60
    detail = client.get(f"{API}/coding/problems/{problems[0]['id']}", headers=headers).json()
    assert detail["test_cases"] and detail["hidden_test_count"] >= 1
    assert len(detail["test_cases"]) + detail["hidden_test_count"] >= 3


def test_submit_awards_xp_once(client, make_user):
    headers = make_user()
    problems = client.get(f"{API}/coding/problems", headers=headers).json()
    fib = next(p for p in problems if p["title"] == "Fibonacci Number")
    code = "class Solution:\n    def fib(self, n):\n        a, b = 0, 1\n        for _ in range(n):\n            a, b = b, a + b\n        return a\n"
    r = client.post(f"{API}/coding/problems/{fib['id']}/submit", headers=headers, json={"code": code, "language": "python"}).json()
    assert r["status"] == "Accepted"
    me = client.get(f"{API}/users/me", headers=headers).json()
    assert me["xp"] == 30 and me["streak"] == 1
    client.post(f"{API}/coding/problems/{fib['id']}/submit", headers=headers, json={"code": code, "language": "python"})
    me2 = client.get(f"{API}/users/me", headers=headers).json()
    assert me2["xp"] == 30 and me2["streak"] == 1


def test_schema_upgrade_adds_columns_without_dropping_data(tmp_path):
    import sqlite3
    from sqlalchemy import create_engine
    from app.core.migrations import upgrade_schema

    db = tmp_path / "old.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR NOT NULL, password_hash VARCHAR NOT NULL)")
    con.execute("INSERT INTO users (email, password_hash) VALUES ('keep@me.com', 'x')")
    con.commit(); con.close()

    upgrade_schema(create_engine(f"sqlite:///{db.as_posix()}"))
    con = sqlite3.connect(db)
    cols = {r[1] for r in con.execute("PRAGMA table_info(users)")}
    assert {"xp", "streak", "last_active_date", "is_admin"} <= cols
    assert con.execute("SELECT email FROM users").fetchall() == [("keep@me.com",)]
