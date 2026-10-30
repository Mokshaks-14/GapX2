from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from app import models
from app.core.security import get_current_user
from app.services import tts

router = APIRouter(prefix="/tts", tags=["Speech"])


class SpeechRequest(BaseModel):
    text: str
    style: str = "teacher"  # "teacher" (concept explainer) or "interviewer"


@router.get("/status")
def tts_status():
    return {"available": tts.available(), "quota_exhausted": tts.quota_exhausted()}


@router.post("")
def synthesize(req: SpeechRequest, user: models.User = Depends(get_current_user)):
    audio = tts.speak(req.text, req.style)
    if audio is None:
        if tts.quota_exhausted():
            raise HTTPException(status_code=429, detail="Today's free natural-voice limit is used up.")
        raise HTTPException(status_code=503, detail="Natural voice is unavailable; the browser voice will be used.")
    return Response(content=audio, media_type="audio/wav", headers={"Cache-Control": "private, max-age=86400"})
