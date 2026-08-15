from typing import List, Optional
from pydantic import BaseModel, Field


class VisionCandidate(BaseModel):
    label: str
    confidence: float


class RecognizeResponse(BaseModel):
    landmark_id: Optional[str]
    landmark_name: Optional[str]
    confidence: float
    candidates: List[VisionCandidate]
    story: Optional[str] = None
    audio_url: Optional[str] = None
    facts: Optional[dict] = None
    validated_by_gps: bool = False
    message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    vision_model_loaded: bool
    num_classes: int
