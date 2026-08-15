"""
PIPELINE ORCHESTRATOR
======================
Drives the fixed, deterministic 5-stage AI pipeline described in
AI_Tourism_Architecture.docx section 4.3:

  Stage 1: Vision        -> candidate landmark(s) + confidence
  Stage 2: GPS Validation -> single validated landmark
  Stage 3: Knowledge DB   -> verified facts
  Stage 4: LLM            -> narrative text
  Stage 5: TTS            -> audio URL

Each stage's output is the next stage's input. No branching, no shared
mutable state — easy to test and to swap out any single stage.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.database.models import Landmark
from app.gps_validation.validator import validate_candidates
from app.llm.narrator import generate_story
from app.tts.speech import synthesize
from app.vision.model import get_vision_service


def run_pipeline(
    image_bytes: bytes,
    db: Session,
    user_lat: Optional[float] = None,
    user_lng: Optional[float] = None,
    language: str = "en",
) -> dict:
    # Stage 1 — Vision
    vision = get_vision_service()
    candidates = vision.predict(image_bytes, top_k=settings.VISION_TOP_K)

    if not candidates:
        return {
            "landmark_id": None,
            "landmark_name": None,
            "confidence": 0.0,
            "candidates": [],
            "validated_by_gps": False,
            "message": "No landmark could be recognized in this image.",
        }

    # Stage 2 — GPS Validation
    all_landmarks = db.query(Landmark).all()
    landmark, validated_by_gps = validate_candidates(
        candidates, user_lat, user_lng, all_landmarks
    )

    if landmark is None:
        top = candidates[0]
        return {
            "landmark_id": None,
            "landmark_name": top["label"],
            "confidence": top["confidence"],
            "candidates": candidates,
            "validated_by_gps": False,
            "message": (
                "Landmark recognized visually but no matching record exists yet "
                "in the knowledge base. Add it via app/database/landmarks_seed.json."
            ),
        }

    top_confidence = next(
        (c["confidence"] for c in candidates if c["label"] == landmark.slug),
        candidates[0]["confidence"],
    )

    # Stage 3 — Knowledge Database
    facts = landmark.to_facts_dict()

    # Stage 4 — LLM narrative rewriting
    story = generate_story(facts, language=language)

    # Stage 5 — Text-to-Speech
    audio_url = synthesize(story, voice=language)

    return {
        "landmark_id": landmark.slug,
        "landmark_name": landmark.name,
        "confidence": top_confidence,
        "candidates": candidates,
        "story": story,
        "audio_url": audio_url,
        "facts": facts,
        "validated_by_gps": validated_by_gps,
    }
