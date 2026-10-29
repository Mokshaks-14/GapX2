from datetime import date, timedelta

from app import models


def record_activity(user: models.User) -> None:
    """Updates the daily streak: +1 for activity on consecutive days, reset to 1 after a gap."""
    today = date.today()
    last = None
    if user.last_active_date:
        try:
            last = date.fromisoformat(user.last_active_date)
        except ValueError:
            last = None
    if last == today:
        return
    user.streak = (user.streak or 0) + 1 if last == today - timedelta(days=1) else 1
    user.last_active_date = today.isoformat()


def add_xp(user: models.User, amount: int) -> bool:
    """Adds XP, updates level and streak. Returns True if the user levelled up."""
    user.xp = max(0, (user.xp or 0) + amount)
    new_level = user.xp // 500 + 1
    levelled = new_level > (user.level or 1)
    user.level = max(1, new_level)
    if amount > 0:
        record_activity(user)
    return levelled
