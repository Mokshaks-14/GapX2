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
    register(client, "Login.Case@gapx.test", password="C0rrect!Pass9")
    assert client.post(f"{API}/auth/login", json={"email": "login.case@gapx.test", "password": "C0rrect!Pass9"}).status_code == 200
    assert client.post(f"{API}/auth/login", json={"email": "login.case@gapx.test", "password": "nope"}).status_code == 400


def admin_headers(client, email="boss@gapx.test", password="Gx!9vQ#tRw42"):
    r = client.post(f"{API}/admin/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_admin_prefix_no_longer_grants_admin(client):
    headers = register(client, "admin.hacker@gapx.test")
    assert client.get(f"{API}/users/me", headers=headers).json()["is_admin"] is False
    assert client.post(f"{API}/admin/auth/login", json={"email": "admin.hacker@gapx.test", "password": "Gx!9vQ#tRw42"}).status_code == 401
    assert client.get(f"{API}/admin/overview", headers=headers).status_code == 401


def test_admin_panel_requires_separate_admin_login(client):
    app_headers = register(client, "boss@gapx.test")             # listed in ADMIN_EMAILS
    assert client.get(f"{API}/users/me", headers=app_headers).json()["is_admin"] is True
    assert client.get(f"{API}/admin/overview", headers=app_headers).status_code == 401   # app token isn't enough
    h = admin_headers(client)
    ov = client.get(f"{API}/admin/overview", headers=h).json()
    assert ov["users"] >= 1 and "flagged_interviews" in ov
    assert client.get(f"{API}/users/me", headers=h).status_code == 401                    # admin token can't use the app
    logs = client.get(f"{API}/admin/logs", headers=h, params={"category": "admin"}).json()
    assert any(l["event"] == "login_success" for l in logs["logs"])
    assert client.get(f"{API}/admin/logs.csv", headers=h).text.startswith("time (UTC)")
    assert client.get(f"{API}/admin/system", headers=h).json()["code_runners"]["python"] is True


def test_admin_can_disable_user_and_failed_logins_are_logged(client):
    victim = register(client, "disable.me@gapx.test")
    victim_id = client.get(f"{API}/users/me", headers=victim).json()["id"]
    try:
        h = admin_headers(client)
    except AssertionError:
        register(client, "boss@gapx.test")
        h = admin_headers(client)
    assert client.post(f"{API}/admin/users/{victim_id}/status", headers=h, json={"active": False, "reason": "test"}).json()["is_active"] is False
    assert client.get(f"{API}/users/me", headers=victim).status_code == 401
    assert client.post(f"{API}/auth/login", json={"email": "disable.me@gapx.test", "password": "Gx!9vQ#tRw42"}).status_code == 403
    client.post(f"{API}/auth/login", json={"email": "disable.me@gapx.test", "password": "wrong"})
    logs = client.get(f"{API}/admin/logs", headers=h, params={"q": "disable.me"}).json()["logs"]
    assert {"login_blocked", "login_failed"} <= {l["event"] for l in logs}


def test_google_login_requires_real_credential(client):
    cfg = client.get(f"{API}/auth/config").json()
    assert cfg["google_client_id"] is None
    # The old endpoint accepted any email; now an unverifiable credential is refused
    r = client.post(f"{API}/auth/google", json={"credential": "fake-token"})
    assert r.status_code in (400, 401, 501)
    assert client.post(f"{API}/auth/google", json={"email": "victim@gapx.test"}).status_code == 422


def test_demo_login_is_gone_and_email_check_works(client):
    assert client.post(f"{API}/auth/demo").status_code in (404, 405)
    assert "demo_login_enabled" not in client.get(f"{API}/auth/config").json()
    register(client, "existing.person@gapx.test")
    assert client.post(f"{API}/auth/check-email", json={"email": "Existing.Person@gapx.test"}).json() == {"exists": True}
    assert client.post(f"{API}/auth/check-email", json={"email": "brand.new@gapx.test"}).json() == {"exists": False}
    assert client.post(f"{API}/auth/check-email", json={"email": "not-an-email"}).status_code == 400


def test_onboarding_details_are_stored_and_used(client, make_user):
    headers = make_user(name="Ravi Kumar")
    client.post(f"{API}/users/onboard", headers=headers, json={
        "role": "Student", "skills": ["Python", "FastAPI"], "target_roles": ["Backend Engineer"],
        "college_name": "PES University", "cgpa": "8.9", "graduation_year": "2026", "phone": "+91 90000 00000",
        "linkedin": "https://linkedin.com/in/ravi", "project_title": "Campus Food Ordering", "project_stack": "FastAPI, Redis",
        "interests": ["Chess"]})
    me = client.get(f"{API}/users/me", headers=headers).json()
    assert me["profile_details"]["college_name"] == "PES University"
    assert me["profile_details"]["project_title"] == "Campus Food Ordering"
    start = client.post(f"{API}/interviews/start", headers=headers, json={
        "target_role": "Backend Engineer", "experience_level": "Fresher", "interview_type": "Technical"}).json()
    assert "Python" in start["first_question"] and start["track"] == "backend"
    iid = start["interview_id"]
    r = client.post(f"{API}/interviews/{iid}/answer", headers=headers, json={"answer": "I am a final year student who likes backend development."}).json()
    assert "Campus Food Ordering" in r["next_question"]


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


def test_jd_match(client, make_user):
    headers = make_user()
    jd = "We are hiring a Frontend Engineer with React, TypeScript, Next.js, REST APIs, Jest testing and Docker experience."
    r = client.post(f"{API}/resumes/jd-match", headers=headers, json={"job_description": jd, "resume": RESUME}).json()
    assert "react" in r["matched_keywords"] and "docker" in r["missing_keywords"]
    assert 0 < r["match_score"] < 100 and r["suggestions"]


def test_daily_challenge_is_stable_and_gives_bonus(client, make_user):
    headers = make_user()
    d1 = client.get(f"{API}/coding/daily", headers=headers).json()
    assert client.get(f"{API}/coding/daily", headers=headers).json()["id"] == d1["id"]
    assert d1["completed_today"] is False and d1["bonus_xp"] == 20


def test_email_domain_rules(monkeypatch):
    from app.services import email_check
    monkeypatch.setattr(email_check, "_has_mail_server", lambda d: d in {"rvce.edu.in", "acme.io"})
    ok = ["me@gmail.com", "me@outlook.com", "me@rvce.edu.in", "me@acme.io"]
    bad = ["me@mygmail.com", "me@gmial.com", "me@yahooo.com", "me@gmail.co", "me@mailinator.com", "me@nomail-here.xyz", "not-an-email"]
    assert all(email_check.validate_signup_email(e) is None for e in ok)
    assert all(email_check.validate_signup_email(e) for e in bad)
    assert "gmail.com" in email_check.validate_signup_email("me@mygmail.com")


def test_signup_rejects_lookalike_domain(client, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "EMAIL_DOMAIN_CHECK", True)
    r = client.post(f"{API}/auth/check-email", json={"email": "someone@mygmail.com"})
    assert r.status_code == 400 and "gmail.com" in r.json()["detail"]
    r = client.post(f"{API}/auth/register", json={"email": "someone@mygmail.com", "password": "secret123", "full_name": "X"})
    assert r.status_code == 400


def test_integrity_events_are_reported(client, make_user):
    headers = make_user()
    iid = client.post(f"{API}/interviews/start", headers=headers, json={
        "target_role": "Software Engineer", "experience_level": "Fresher", "interview_type": "Technical", "num_questions": 5}).json()["interview_id"]
    r = client.post(f"{API}/interviews/{iid}/answer", headers=headers, json={
        "answer": "I am a computer science student who built a chat app with Python.", "integrity_events": ["multiple_faces", "background_motion"]}).json()
    assert r["speech_parts"] and len(r["speech_parts"]) == 2
    client.post(f"{API}/interviews/{iid}/answer", headers=headers, json={"answer": "Thank you, I would like to conclude the interview."})
    fb = client.get(f"{API}/interviews/{iid}/feedback", headers=headers).json()
    integ = fb["behavior_scores"]["integrity"]
    assert integ["flagged"] is True and integ["counts"]["multiple_faces"] == 1 and "question 1" in integ["summary"]


def test_realtime_integrity_events_are_logged(client, make_user):
    headers = make_user()
    iid = client.post(f"{API}/interviews/start", headers=headers, json={
        "target_role": "Software Engineer", "experience_level": "Fresher", "interview_type": "Technical", "num_questions": 5}).json()["interview_id"]
    assert client.post(f"{API}/interviews/{iid}/integrity", headers=headers, json={"type": "phone_detected", "question_number": 1}).json()["ok"]
    assert client.post(f"{API}/interviews/{iid}/integrity", headers=headers, json={"type": "nonsense"}).status_code == 400
    client.post(f"{API}/interviews/{iid}/answer", headers=headers, json={"answer": "Thank you, I would like to conclude the interview."})
    integ = client.get(f"{API}/interviews/{iid}/feedback", headers=headers).json()["behavior_scores"]["integrity"]
    assert integ["counts"]["phone_detected"] == 1 and integ["flagged"] is True



def test_password_and_onboarding_rules(client, make_user):
    from app.services.validation import password_problem
    assert password_problem("short")
    assert password_problem("alllowercase1!")
    assert password_problem("Password123!")            # too common
    assert password_problem("Ravi@2026x", name="Ravi Kumar")  # contains name
    assert password_problem("Str0ng!Pass#") is None
    r = client.post(f"{API}/auth/register", json={"email": "weak.pw@gapx.test", "password": "abc12345", "full_name": "Weak Pw"})
    assert r.status_code == 400 and "uppercase" in r.json()["detail"]
    headers = make_user()
    r = client.post(f"{API}/users/onboard", headers=headers, json={
        "role": "Student", "target_roles": ["Backend Engineer"], "college_name": "X", "phone": "12",
        "linkedin": "https://evil.com/x", "cgpa": "14", "graduation_year": "20x6"})
    detail = r.json()["detail"]
    assert r.status_code == 400 and "phone" in detail and "LinkedIn" in detail and "CGPA" in detail and "Graduation year" in detail


def test_email_verification_code_flow(client, monkeypatch):
    from app.core.config import settings
    from app.services import email_verification
    monkeypatch.setattr(settings, "EMAIL_VERIFICATION_REQUIRED", True)
    sent = {}
    monkeypatch.setattr(email_verification, "smtp_configured", lambda: True)
    monkeypatch.setattr(email_verification, "_send_email", lambda to, code: sent.update({to: code}))
    email = "verify.me@gapx.test"
    body = {"email": email, "password": "Gx!9vQ#tRw42", "full_name": "Verify Me"}

    assert client.post(f"{API}/auth/register", json=body).status_code == 400            # no code yet
    assert client.post(f"{API}/auth/send-code", json={"email": email}).json()["sent"] is True
    assert client.post(f"{API}/auth/send-code", json={"email": email}).status_code == 429  # resend cooldown
    r = client.post(f"{API}/auth/register", json={**body, "verification_code": "000000" if sent[email] != "000000" else "111111"})
    assert r.status_code == 400 and "isn't right" in r.json()["detail"]
    r = client.post(f"{API}/auth/register", json={**body, "verification_code": sent[email]})
    assert r.status_code == 200 and r.json()["email"] == email


def _admin(client):
    try:
        return admin_headers(client)
    except AssertionError:
        register(client, "boss@gapx.test")
        return admin_headers(client)


def test_admin_can_add_coding_problem_that_students_can_solve(client, make_user):
    h = _admin(client)
    ref = "class Solution:\n    def doubleAll(self, nums):\n        return [x * 2 for x in nums]\n"
    body = {"title": "Double Everything", "difficulty": "Easy", "category": "Arrays", "statement": "Double each number.",
            "fn": "doubleAll", "params": [["nums", "int[]"]], "returns": "int[]", "reference_solution": ref,
            "tests": [{"input": "[1,2]", "output": ""}, {"input": "[5]", "output": "10"}, {"input": "[0,-3]", "output": "", "is_hidden": True}]}
    r = client.post(f"{API}/admin/problems", headers=h, json=body)
    assert r.status_code == 200, r.text
    pid = r.json()["id"]
    assert [t["output"] for t in r.json()["tests"]] == ["2,4", "10", "0,-6"]          # filled from the reference
    bad = dict(body, title="Wrong Expected", tests=[{"input": "[1]", "output": "3"}, {"input": "[2]", "output": "4"}])
    assert "reference solution returns" in client.post(f"{API}/admin/problems", headers=h, json=bad).json()["detail"]
    assert client.post(f"{API}/admin/problems", headers=h, json=dict(body, tests=body["tests"][:1])).status_code == 400
    assert client.post(f"{API}/admin/problems", headers=make_user(), json=body).status_code == 401   # students can't add

    student = make_user()
    p = client.get(f"{API}/coding/problems/{pid}", headers=student).json()
    assert p["hidden_test_count"] == 1 and "doubleAll" in p["starter_code_java"] and "doubleAll" in p["starter_code_js"]
    assert client.post(f"{API}/coding/problems/{pid}/submit", headers=student, json={"code": ref, "language": "python"}).json()["status"] == "Accepted"

    assert client.delete(f"{API}/admin/problems/1", headers=h).status_code == 400       # built-in problems stay
    assert client.delete(f"{API}/admin/problems/{pid}", headers=h).json()["ok"]
    assert client.get(f"{API}/coding/problems/{pid}", headers=student).status_code == 404


def test_admin_interview_question_is_asked(client, make_user):
    h = _admin(client)
    q = client.post(f"{API}/admin/interview-questions", headers=h, json={
        "track": "frontend", "topic": "React Hooks", "level": "Easy",
        "question": "What does the useEffect hook do in React, and when does it run?",
        "key_points": ["side effects, side effect", "dependency array, dependencies"],
        "ideal_answer": "useEffect runs side effects after render; the dependency array controls when it runs again."}).json()
    student = make_user()
    iid = client.post(f"{API}/interviews/start", headers=student, json={
        "target_role": "Frontend Engineer", "experience_level": "Fresher", "interview_type": "Technical", "num_questions": 5}).json()["interview_id"]
    seen = []
    for ans in ["Hi, I build dashboards in React and JavaScript.", "I am not sure.", "I don't know."]:
        seen.append(client.post(f"{API}/interviews/{iid}/answer", headers=student, json={"answer": ans}).json().get("speech_text_to_speak", ""))
    assert any("useEffect" in s for s in seen)
    assert client.delete(f"{API}/admin/interview-questions/{q['id']}", headers=h).json()["ok"]


def test_blocked_paste_is_logged(client, make_user):
    student = make_user()
    assert client.post(f"{API}/coding/problems/1/clipboard-blocked", headers=student, json={"action": "paste"}).json()["ok"]
    assert client.post(f"{API}/coding/problems/1/clipboard-blocked", headers=student, json={"action": "hack"}).status_code == 400
    logs = client.get(f"{API}/admin/logs", headers=_admin(client), params={"category": "coding"}).json()["logs"]
    assert any(l["event"] == "paste_blocked" for l in logs)
