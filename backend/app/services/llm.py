"""Single entry point for calling a hosted LLM.

Order of preference: Google Gemini (google-genai SDK) -> OpenAI -> None.
When nothing is configured (or every call fails) callers get None and fall back
to GapX's built-in offline engines, so the app keeps working without API keys.
"""
import json
import logging
import re
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_gemini_client = None
_legacy_genai = None
_openai_client = None

if settings.GEMINI_API_KEY:
    try:
        from google import genai  # google-genai (current SDK)
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info("Gemini ready (google-genai, model %s).", settings.GEMINI_MODEL)
    except Exception as e:  # pragma: no cover - depends on installed packages
        try:
            import google.generativeai as legacy  # deprecated SDK, kept as a fallback
            legacy.configure(api_key=settings.GEMINI_API_KEY)
            _legacy_genai = legacy
            logger.info("Gemini ready (legacy google-generativeai SDK).")
        except Exception:
            logger.warning("Gemini key set but no Gemini SDK could be loaded: %s", e)

if settings.OPENAI_API_KEY:
    try:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30)
        logger.info("OpenAI ready (model %s).", settings.OPENAI_MODEL)
    except Exception as e:  # pragma: no cover
        logger.warning("OpenAI key set but the client failed to initialise: %s", e)


def is_available() -> bool:
    return bool(_gemini_client or _legacy_genai or _openai_client)


def _gemini(prompt: str, want_json: bool) -> Optional[str]:
    if _gemini_client is not None:
        from google.genai import types
        config = types.GenerateContentConfig(response_mime_type="application/json") if want_json else None
        resp = _gemini_client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt, config=config)
        return resp.text
    if _legacy_genai is not None:
        cfg = {"response_mime_type": "application/json"} if want_json else None
        model = _legacy_genai.GenerativeModel(settings.GEMINI_MODEL, generation_config=cfg)
        return model.generate_content(prompt).text
    return None


def _openai(prompt: str, want_json: bool) -> Optional[str]:
    if _openai_client is None:
        return None
    kwargs: dict = {}
    if want_json:
        kwargs["response_format"] = {"type": "json_object"}
    resp = _openai_client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        **kwargs,
    )
    return resp.choices[0].message.content


def generate_text(prompt: str) -> Optional[str]:
    for provider in (_gemini, _openai):
        try:
            text = provider(prompt, False)
            if text and text.strip():
                return text.strip()
        except Exception as e:
            logger.warning("LLM text call failed (%s): %s", provider.__name__, e)
    return None


def parse_json(raw: Optional[str]) -> Any:
    if not raw:
        return None
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Pull the first JSON object/array out of surrounding prose
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
    return None


def generate_json(prompt: str) -> Any:
    """Returns parsed JSON from the first provider that produces valid JSON, else None."""
    for provider in (_gemini, _openai):
        try:
            parsed = parse_json(provider(prompt, True))
            if parsed is not None:
                return parsed
        except Exception as e:
            logger.warning("LLM JSON call failed (%s): %s", provider.__name__, e)
    return None
