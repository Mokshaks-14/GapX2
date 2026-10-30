"""Single entry point for calling a language model.

Order of preference: Google Gemini (with model fallbacks) -> OpenAI -> local Ollama -> None.
When nothing is available, callers get None and fall back to GapX's built-in offline engines,
so the app keeps working without API keys or internet.
"""
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

_gemini_client = None
_openai_client = None
_ollama_checked_at = 0.0
_ollama_ok = False
_dead_models: Dict[str, float] = {}  # model -> time it failed (retired/overloaded), skipped for a while

if settings.GEMINI_API_KEY:
    try:
        from google import genai
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info("Gemini ready (model %s).", settings.GEMINI_MODEL)
    except Exception as e:  # pragma: no cover
        logger.warning("Gemini key set but the google-genai SDK failed to load: %s", e)

if settings.OPENAI_API_KEY:
    try:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30)
    except Exception as e:  # pragma: no cover
        logger.warning("OpenAI key set but the client failed to initialise: %s", e)


def _gemini_models(fast: bool = False) -> List[str]:
    first = [settings.GEMINI_FAST_MODEL] if fast and settings.GEMINI_FAST_MODEL else []
    models = first + [settings.GEMINI_MODEL] + [m.strip() for m in settings.GEMINI_FALLBACK_MODELS.split(",") if m.strip()]
    now = time.time()
    # Skip a model for 10 minutes after it reports retired/overloaded
    return [m for i, m in enumerate(models) if m not in models[:i] and now - _dead_models.get(m, 0) > 600]


def _ollama_available() -> bool:
    global _ollama_checked_at, _ollama_ok
    if time.time() - _ollama_checked_at < 60:
        return _ollama_ok
    _ollama_checked_at = time.time()
    try:
        _ollama_ok = requests.get(f"{settings.OLLAMA_URL}/api/tags", timeout=1.5).status_code == 200
    except requests.RequestException:
        _ollama_ok = False
    return _ollama_ok


def is_available() -> bool:
    return bool(_gemini_client or _openai_client) or _ollama_available()


def provider_name() -> str:
    if _gemini_client:
        return "gemini"
    if _openai_client:
        return "openai"
    if _ollama_available():
        return "ollama"
    return "offline"


# ─── provider calls (all take a list of chat messages) ───
def _gemini(messages: List[Dict[str, str]], want_json: bool, fast: bool = False) -> Optional[str]:
    if _gemini_client is None:
        return None
    from google.genai import types
    system = "\n".join(m["content"] for m in messages if m["role"] == "system") or None
    contents = [types.Content(role="model" if m["role"] == "assistant" else "user", parts=[types.Part(text=m["content"])])
                for m in messages if m["role"] != "system"]
    config = types.GenerateContentConfig(system_instruction=system,
                                         response_mime_type="application/json" if want_json else None)
    last_error: Optional[Exception] = None
    for model in _gemini_models(fast):
        try:
            resp = _gemini_client.models.generate_content(model=model, contents=contents, config=config)
            if resp.text:
                return resp.text
        except Exception as e:
            last_error = e
            text = str(e)
            if "404" in text or "503" in text or "UNAVAILABLE" in text or "NOT_FOUND" in text:
                _dead_models[model] = time.time()
            logger.warning("Gemini model %s failed: %s", model, text[:200])
    if last_error:
        raise last_error
    return None


def _openai(messages: List[Dict[str, str]], want_json: bool, fast: bool = False) -> Optional[str]:
    if _openai_client is None:
        return None
    kwargs: dict = {"response_format": {"type": "json_object"}} if want_json else {}
    resp = _openai_client.chat.completions.create(model=settings.OPENAI_MODEL, messages=messages, temperature=0.6, **kwargs)
    return resp.choices[0].message.content


def _ollama(messages: List[Dict[str, str]], want_json: bool, fast: bool = False) -> Optional[str]:
    if not _ollama_available():
        return None
    body: Dict[str, Any] = {"model": settings.OLLAMA_MODEL, "messages": messages, "stream": False}
    if want_json:
        body["format"] = "json"
    resp = requests.post(f"{settings.OLLAMA_URL}/api/chat", json=body, timeout=120)
    resp.raise_for_status()
    return resp.json().get("message", {}).get("content")


PROVIDERS = (_gemini, _openai, _ollama)


def chat(messages: List[Dict[str, str]], want_json: bool = False, fast: bool = False) -> Optional[str]:
    """Multi-turn chat. messages: [{"role": "system"|"user"|"assistant", "content": "..."}]."""
    for provider in PROVIDERS:
        try:
            text = provider(messages, want_json, fast)
            if text and text.strip():
                return text.strip()
        except Exception as e:
            logger.warning("LLM call failed (%s): %s", provider.__name__, str(e)[:200])
    return None


def generate_text(prompt: str, fast: bool = False) -> Optional[str]:
    return chat([{"role": "user", "content": prompt}], fast=fast)


def parse_json(raw: Optional[str]) -> Any:
    if not raw:
        return None
    text = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
    return None


def generate_json(prompt: str, fast: bool = False) -> Any:
    """Parsed JSON from the first provider that returns valid JSON, else None."""
    for provider in PROVIDERS:
        try:
            parsed = parse_json(provider([{"role": "user", "content": prompt}], True, fast))
            if parsed is not None:
                return parsed
        except Exception as e:
            logger.warning("LLM JSON call failed (%s): %s", provider.__name__, str(e)[:200])
    return None
