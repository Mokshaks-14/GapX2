"""Checks that a sign-up email uses a real, trustworthy domain.

Accepted: well-known providers (gmail.com, outlook.com, ...) and real organisation domains
(colleges, companies) that can receive email (they have MX records).
Rejected: look-alikes of big providers (mygmail.com, gmial.com, yahooo.com, gmail.co),
disposable inbox services, and domains that can't receive email.
"""
import logging
import re
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@([A-Za-z0-9\-]+\.)+[A-Za-z]{2,}$")

TRUSTED_PROVIDERS = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com", "msn.com", "outlook.in", "hotmail.co.uk",
    "yahoo.com", "yahoo.in", "yahoo.co.in", "yahoo.co.uk", "ymail.com", "rocketmail.com", "icloud.com", "me.com", "mac.com",
    "proton.me", "protonmail.com", "pm.me", "zoho.com", "zohomail.in", "aol.com", "gmx.com", "gmx.net", "mail.com",
    "rediffmail.com", "yandex.com", "tutanota.com", "fastmail.com", "hey.com",
}
# Provider names that impostor domains like to borrow
PROVIDER_NAMES = {"gmail": "gmail.com", "googlemail": "googlemail.com", "outlook": "outlook.com", "hotmail": "hotmail.com",
                  "yahoo": "yahoo.com", "icloud": "icloud.com", "protonmail": "protonmail.com", "rediffmail": "rediffmail.com",
                  "zoho": "zoho.com", "aol": "aol.com"}
DISPOSABLE = {
    "mailinator.com", "10minutemail.com", "10minutemail.net", "tempmail.com", "temp-mail.org", "guerrillamail.com",
    "guerrillamail.net", "sharklasers.com", "yopmail.com", "trashmail.com", "getnada.com", "dispostable.com", "maildrop.cc",
    "throwawaymail.com", "fakeinbox.com", "mintemail.com", "mohmal.com", "emailondeck.com", "tempmailo.com", "moakt.com",
    "burnermail.io", "spamgourmet.com", "mailnesia.com", "tempr.email", "discard.email", "inboxkitten.com", "1secmail.com",
}


def _distance(a: str, b: str) -> int:
    """Levenshtein edit distance (small strings only)."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def lookalike_of(domain: str) -> Optional[str]:
    """Returns the real provider a domain imitates (e.g. mygmail.com -> gmail.com), else None."""
    if domain in TRUSTED_PROVIDERS:
        return None
    name = domain.split(".")[0]
    for word, real in PROVIDER_NAMES.items():
        if word in domain.replace(".", "") and len(word) >= 4:
            return real                          # mygmail.com, gmail.co, gmail-mail.com, yahoo.xyz
    for real in sorted(TRUSTED_PROVIDERS, key=lambda d: (not d.endswith(".com"), d)):
        real_name = real.split(".")[0]
        swapped = len(name) == len(real_name) and sorted(name) == sorted(real_name) and _distance(name, real_name) == 2
        if len(real_name) >= 5 and (_distance(name, real_name) <= 1 or swapped):
            return real                          # gmial.com, yahooo.com, outlok.com, hotmial.com
    return None


@lru_cache(maxsize=2048)
def _has_mail_server(domain: str) -> Optional[bool]:
    """True/False if DNS gives a clear answer, None if DNS couldn't be reached."""
    try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.lifetime = 4.0
        try:
            return len(resolver.resolve(domain, "MX")) > 0
        except dns.resolver.NoAnswer:
            # No MX but an A record can still receive mail (RFC 5321 fallback); treat as unverified
            return False
        except dns.resolver.NXDOMAIN:
            return False
    except Exception as e:  # network down, DNS timeout, dnspython missing
        logger.warning("Email domain check couldn't reach DNS for %s: %s", domain, e)
        return None


def validate_signup_email(email: str) -> Optional[str]:
    """Returns an error message for an unacceptable email, or None if it's fine."""
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email):
        return "Please enter a valid email address."
    domain = email.split("@", 1)[1]
    if domain in TRUSTED_PROVIDERS:
        return None
    if domain in DISPOSABLE or any(domain.endswith("." + d) for d in DISPOSABLE):
        return "Temporary or disposable email addresses aren't allowed. Please use your personal, college or work email."
    real = lookalike_of(domain)
    if real:
        return f"'{domain}' isn't a recognised email provider. Did you mean {real}?"
    has_mx = _has_mail_server(domain)
    if has_mx is False:
        return f"'{domain}' can't receive email. Please use a real personal, college or work email address."
    return None  # has a mail server, or DNS was unreachable (don't block real users when offline)
