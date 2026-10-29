"""The complete coding problem bank: the original 30 problems (with signature fixes) + the extra problems."""
from app.services.problem_data import PROBLEMS_DATA as _ORIGINAL
from app.services.problems_extra import _build_extra, apply_original_fixes

ALL_PROBLEMS = apply_original_fixes(_ORIGINAL) + _build_extra(start_id=len(_ORIGINAL) + 1)
