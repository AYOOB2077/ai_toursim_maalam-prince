"""
LAYER 6 — BACKEND API (Control Plane)
=======================================
This is the only piece your mobile/cloud app talks to. It receives an image
+ GPS from your existing app, drives the 5-stage AI pipeline, and returns
JSON (story text + audio URL). It does not render any UI — you already have
the app.

Run locally:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Endpoints:
    POST /recognize   -> main pipeline endpoint, called by the mobile app
    GET  /health       -> readiness check (also used by cloud load balancers)
    GET  /audio/{file}  -> serves cached generated MP3s (swap for S3/CDN in prod)
"""
import logging
import os

from fastapi import Depends, FastAPI, File, Form, HTTPException, Header, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import get_db, init_db
from app.orchestrator import run_pipeline
from app.schemas import HealthResponse, RecognizeResponse
from app.vision.model import get_vision_service

from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Warm up the vision model once at boot instead of on the first request.
    try:
        get_vision_service()
        logger.info("Vision model loaded successfully.")
    except Exception as exc:
        logger.error("Vision model failed to load at startup: %s", exc)
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# Loosen in production to your actual app domains only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def check_api_key(x_api_key: str | None = Header(default=None)):
    """Simple shared-secret auth. Skipped if API_KEY is unset (local dev)."""
    if settings.API_KEY and x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header.")


@app.get("/health", response_model=HealthResponse)
def health():
    try:
        vision = get_vision_service()
        return HealthResponse(
            status="ok", vision_model_loaded=True, num_classes=len(vision.class_names)
        )
    except Exception as exc:
        return HealthResponse(status=f"vision_error: {exc}", vision_model_loaded=False, num_classes=0)


@app.post("/recognize", response_model=RecognizeResponse, dependencies=[Depends(check_api_key)])
async def recognize(
    image: UploadFile = File(..., description="Landmark photo, JPEG/PNG"),
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
    language: str = Form(default="en"),
    db: Session = Depends(get_db),
):
    """
    Main pipeline entry point called by the mobile app:
    Vision -> GPS Validation -> Knowledge DB -> LLM -> TTS.
    """
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image upload.")

    result = run_pipeline(
        image_bytes=image_bytes,
        db=db,
        user_lat=latitude,
        user_lng=longitude,
        language=language,
    )
    return RecognizeResponse(**result)


@app.get("/audio/{filename}")
def get_audio(filename: str):
    path = os.path.join(settings.AUDIO_CACHE_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Audio file not found.")
    return FileResponse(path, media_type="audio/mpeg")
