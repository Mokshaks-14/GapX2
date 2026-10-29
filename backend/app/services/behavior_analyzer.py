from typing import Any, Dict, List, Optional


def _clamp(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return min(max(float(value), 0.0), 1.0)


class BehaviorAnalyzer:
    """Turns face-analysis metrics measured in the browser into interview behavior scores.

    The browser runs MediaPipe Face Landmarker on the webcam feed and sends attention, smile,
    stress (brow tension) and eye-contact ratios between 0 and 1. When the camera is off or the
    model can't load, the metrics are None and no face-based scores are produced.
    """

    @staticmethod
    def analyze_frame_telemetry(attention: Optional[float], smile: Optional[float], stress: Optional[float],
                                eye_contact: Optional[float]) -> Dict[str, Any]:
        attention, smile, stress, eye_contact = map(_clamp, (attention, smile, stress, eye_contact))
        if attention is None or eye_contact is None:
            return {"has_face_data": False}

        smile = smile if smile is not None else 0.3
        stress = stress if stress is not None else 0.2
        confidence = attention * 0.4 + eye_contact * 0.4 + (1 - stress) * 0.2
        engagement = attention * 0.6 + smile * 0.2 + eye_contact * 0.2

        if stress > 0.6:
            emotion = "Tense"
        elif smile > 0.4:
            emotion = "Positive / Relaxed"
        elif attention < 0.4:
            emotion = "Distracted"
        else:
            emotion = "Focused / Neutral"

        return {
            "has_face_data": True,
            "attention_score": round(attention * 100, 1),
            "smile_score": round(smile * 100, 1),
            "stress_score": round(stress * 100, 1),
            "eye_contact_score": round(eye_contact * 100, 1),
            "confidence_score": round(confidence * 100, 1),
            "engagement_score": round(engagement * 100, 1),
            "detected_emotion": emotion,
        }

    @staticmethod
    def get_aggregate_behavior_report(session: List[Dict[str, Any]]) -> Dict[str, Any]:
        frames = [x for x in session if x.get("has_face_data")]
        if not frames:
            return {
                "has_face_data": False,
                "overall_behavior_rating": "Not measured",
                "body_language_feedback": "Camera analysis wasn't available for this session, so no body-language scores were recorded.",
            }

        def avg(key: str) -> float:
            return round(sum(f[key] for f in frames) / len(frames), 1)

        att, sml, strs, eye, conf = avg("attention_score"), avg("smile_score"), avg("stress_score"), avg("eye_contact_score"), avg("confidence_score")
        if strs > 45 or att < 60:
            rating = "Needs Improvement"
        elif att < 80 or eye < 70:
            rating = "Good"
        else:
            rating = "Excellent"

        tips = []
        if eye < 70:
            tips.append("Look at the camera more often; it reads as eye contact to the interviewer.")
        if att < 70:
            tips.append("Keep your face centred and avoid looking away for long periods.")
        if strs > 40:
            tips.append("Your brow looked tense at times. Slow breathing before answering helps you appear calmer.")
        if sml < 15:
            tips.append("An occasional smile, especially when greeting and closing, comes across as confident and friendly.")

        return {
            "has_face_data": True,
            "avg_attention": att, "avg_smile": sml, "avg_stress": strs, "avg_eye_contact": eye, "avg_confidence": conf,
            "overall_behavior_rating": rating,
            "body_language_feedback": " ".join(tips) or "Steady eye contact and composed expression throughout. Well done.",
            "disclaimer": "Estimated from facial landmarks in your browser; treat it as a self-improvement guide, not an exact measurement.",
        }
