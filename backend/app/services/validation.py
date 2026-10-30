"""Server-side rules for sign-up and onboarding fields (the frontend checks the same rules first)."""
import re
from datetime import date
from typing import List, Optional

COMMON_PASSWORDS = {
    "password", "password1", "password123", "123456", "12345678", "123456789", "1234567890", "qwerty", "qwerty123",
    "abc123", "111111", "iloveyou", "admin", "admin123", "welcome", "welcome1", "letmein", "monkey", "dragon",
    "football", "sunshine", "princess", "passw0rd", "p@ssw0rd", "p@ssword", "india123", "test1234", "changeme",
}

PASSWORD_RULES = [
    (lambda p: len(p) >= 8, "at least 8 characters"),
    (lambda p: re.search(r"[A-Z]", p), "an uppercase letter"),
    (lambda p: re.search(r"[a-z]", p), "a lowercase letter"),
    (lambda p: re.search(r"\d", p), "a number"),
    (lambda p: re.search(r"[^A-Za-z0-9]", p), "a special character (like ! @ # $)"),
    (lambda p: not re.search(r"\s", p), "no spaces"),
]


def password_problem(password: str, email: str = "", name: str = "") -> Optional[str]:
    password = password or ""
    missing = [label for rule, label in PASSWORD_RULES if not rule(password)]
    if missing:
        return "Password needs " + ", ".join(missing) + "."
    if len(password) > 72:
        return "Password must be 72 characters or fewer."
    lowered = password.lower()
    if lowered in COMMON_PASSWORDS or re.sub(r"[^a-z]", "", lowered) in COMMON_PASSWORDS:
        return "That password is too common. Please choose something harder to guess."
    local = (email or "").split("@")[0].lower()
    if len(local) >= 4 and local in lowered:
        return "Password shouldn't contain your email address."
    for part in (name or "").lower().split():
        if len(part) >= 4 and part in lowered:
            return "Password shouldn't contain your name."
    if re.search(r"(.)\1{3,}", password):
        return "Password shouldn't repeat the same character 4 or more times."
    return None


def name_problem(name: str) -> Optional[str]:
    name = (name or "").strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z .'\-]{1,59}", name):
        return "Please enter your real name (letters, spaces, . ' - only, 2–60 characters)."
    if len(name.replace(" ", "")) < 2:
        return "Please enter your full name."
    return None


def onboarding_problems(d: dict) -> List[str]:
    """Returns readable problems with onboarding data (empty list when everything is fine)."""
    problems = []
    roles = d.get("target_roles") or []
    if not roles:
        problems.append("Choose at least one target job role.")
    if len(d.get("skills") or []) > 40:
        problems.append("Please list at most 40 skills.")
    if any(len(str(s)) > 40 for s in d.get("skills") or []):
        problems.append("Each skill should be 40 characters or fewer.")

    phone = (d.get("phone") or "").strip()
    if phone:
        digits = re.sub(r"\D", "", phone)
        if not re.fullmatch(r"\+?[\d\s\-()]{7,20}", phone) or not 10 <= len(digits) <= 15:
            problems.append("Enter a valid phone number (10–15 digits, optional + country code).")

    patterns = {
        "linkedin": (r"^(https?://)?(www\.|[a-z]{2}\.)?linkedin\.com/in/[A-Za-z0-9_\-%.]{3,100}/?$", "LinkedIn URL like https://linkedin.com/in/your-name"),
        "github": (r"^(https?://)?(www\.)?github\.com/[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/?$", "GitHub URL like https://github.com/username"),
        "portfolio": (r"^https?://[^\s/$.?#].[^\s]*$", "website URL starting with http:// or https://"),
    }
    for field, (pattern, label) in patterns.items():
        value = (d.get(field) or "").strip()
        if value and not re.match(pattern, value, re.IGNORECASE):
            problems.append(f"Enter a valid {label}.")

    cgpa = d.get("cgpa")
    if cgpa not in (None, ""):
        try:
            value = float(str(cgpa).replace("%", ""))
            if not (0 <= value <= 10 or (str(cgpa).strip().endswith("%") and 0 <= value <= 100)):
                raise ValueError
        except ValueError:
            problems.append("CGPA must be between 0 and 10 (or a percentage like 85%).")

    year = (d.get("graduation_year") or "").strip()
    if year:
        if not re.fullmatch(r"\d{4}", year) or not 1980 <= int(year) <= date.today().year + 6:
            problems.append(f"Graduation year must be a 4-digit year between 1980 and {date.today().year + 6}.")

    if (d.get("role") or "Student") == "Student" and not (d.get("college_name") or "").strip():
        problems.append("Enter your college or university name.")
    if (d.get("role") == "Working Professional") and not (d.get("current_company") or "").strip():
        problems.append("Enter your current company.")

    title = (d.get("project_title") or "").strip()
    if title and not 3 <= len(title) <= 80:
        problems.append("Project name should be 3–80 characters.")
    if len(d.get("project_description") or "") > 1200:
        problems.append("Project description should be under 1200 characters.")
    if (d.get("project_description") or "").strip() and not title:
        problems.append("Add a project name for the project you described.")
    try:
        hours = int(d.get("preferred_learning_hours") or 2)
        if not 1 <= hours <= 16:
            raise ValueError
    except (TypeError, ValueError):
        problems.append("Daily study hours must be between 1 and 16.")
    return problems
