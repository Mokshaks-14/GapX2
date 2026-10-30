"""Plain-language explanations and extra interview Q&A for every roadmap topic."""
from app.services.notes.core import NOTES as _CORE
from app.services.notes.data import NOTES as _DATA
from app.services.notes.ops import NOTES as _OPS
from app.services.notes.web import NOTES as _WEB

EXPLAINED = {**_CORE, **_WEB, **_DATA, **_OPS}
