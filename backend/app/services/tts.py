"""Natural-sounding speech via Gemini text-to-speech, with an on-disk cache.

Returns WAV bytes, or None when no TTS model is available (the browser voice is used instead).
"""
import hashlib
import io
import logging
import re
import threading
import time
import wave
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from app.core.config import BASE_DIR, settings
from app.services import llm

logger = logging.getLogger(__name__)
CACHE_DIR = BASE_DIR / "tts_cache"

# One voice everywhere (explainer and interviewer): Gemini's "Kore" with a warm, natural delivery.
VOICE_NAME = "Kore"
DELIVERY = "Read this naturally and warmly, like a friendly teacher explaining to a student, with natural pauses:"
CACHE_STYLE = "teacher"  # cache key kept stable so audio already generated is reused

# Every Gemini TTS model offers the same "Kore" voice and has its own free daily quota,
# so we rotate through them before giving up.
_exhausted_until = {}  # model -> unix time when its quota resets
_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="tts")
_inflight: dict = {}   # cache key -> Future, so the same text is never generated twice at once
_lock = threading.Lock()


def _models():
    chain = [settings.GEMINI_TTS_MODEL] + [m.strip() for m in settings.GEMINI_TTS_FALLBACK_MODELS.split(",") if m.strip()]
    now = time.time()
    return [m for i, m in enumerate(chain) if m and m not in chain[:i] and _exhausted_until.get(m, 0) < now]


def quota_exhausted() -> bool:
    return available() and not _models()


def _wav(pcm: bytes, rate: int = 24000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


def available() -> bool:
    return llm._gemini_client is not None and bool(settings.GEMINI_TTS_MODEL)


def _retry_seconds(error: str) -> float:
    m = re.search(r"retryDelay'?:\s*'?(\d+)s", error)
    return float(m.group(1)) if m else 3600.0


def _key(text: str) -> str:
    return hashlib.sha256(f"{settings.GEMINI_TTS_MODEL}|{CACHE_STYLE}|{text}".encode()).hexdigest()


def _clean(text: str) -> str:
    return " ".join((text or "").split())[:2400]


def _submit(text: str) -> Optional[Future]:
    key = _key(text)
    if (CACHE_DIR / f"{key}.wav").exists():
        return None
    with _lock:
        fut = _inflight.get(key)
        if fut is None:
            fut = _pool.submit(_generate, text, key)
            _inflight[key] = fut
            fut.add_done_callback(lambda _f, k=key: _inflight.pop(k, None))
        return fut


def warm(text: str) -> None:
    """Starts generating audio in the background so it's ready when the browser asks for it."""
    text = _clean(text)
    if text and available() and _models():
        _submit(text)


def speak(text: str, style: str = "teacher") -> Optional[bytes]:
    text = _clean(text)
    if not text or not available():
        return None
    cached = CACHE_DIR / f"{_key(text)}.wav"
    if cached.exists():
        return cached.read_bytes()
    fut = _submit(text)
    if fut is None:
        return cached.read_bytes() if cached.exists() else None
    return fut.result()


def _generate(text: str, key: str) -> Optional[bytes]:
    cached = CACHE_DIR / f"{key}.wav"
    from google.genai import types
    for model in _models():
        try:
            resp = llm._gemini_client.models.generate_content(
                model=model,
                contents=f"{DELIVERY} {text}",
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE_NAME))),
                ),
            )
            part = resp.candidates[0].content.parts[0].inline_data
            rate = 24000
            if part.mime_type and "rate=" in part.mime_type:
                try:
                    rate = int(part.mime_type.split("rate=")[1].split(";")[0])
                except ValueError:
                    pass
            audio = _wav(part.data, rate)
            CACHE_DIR.mkdir(exist_ok=True)
            cached.write_bytes(audio)
            return audio
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                _exhausted_until[model] = time.time() + _retry_seconds(err)
                logger.warning("TTS quota used up for %s; trying the next voice model.", model)
            elif "404" in err or "NOT_FOUND" in err:
                _exhausted_until[model] = time.time() + 86400
            else:
                logger.warning("TTS failed on %s: %s", model, err[:200])
    return None
