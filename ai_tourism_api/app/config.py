"""
Central configuration for the AI Tourism Backend API.
Every value can be overridden with an environment variable (see .env.example).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent

# Load .env file automatically
load_dotenv(BASE_DIR / ".env")


class Settings:
    # --- General -------------------------------------------------------
    APP_NAME: str = "AI Tourism Backend API"
    ENV: str = os.getenv("ENV", "development")  # development | production
    API_KEY: str = os.getenv("API_KEY", "")  # simple shared-secret auth for the mobile app

    # --- Vision (Layer 1) -----------------------------------------------
    # Option A (default): load from a local file baked into the image/repo.
    VISION_MODEL_PATH: str = os.getenv(
        "VISION_MODEL_PATH", str(APP_DIR / "vision" / "best_tourism_model.keras")
    )
    # Option B: load from Hugging Face Hub instead. If VISION_HF_REPO_ID is
    # set, model.py downloads the file from the Hub at startup and ignores
    # VISION_MODEL_PATH.
    VISION_HF_REPO_ID: str = os.getenv("VISION_HF_REPO_ID", "")  # e.g. "yourname/tourism-model"
    VISION_HF_FILENAME: str = os.getenv("VISION_HF_FILENAME", "best_tourism_model.keras")
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")  # only needed for private repos
    VISION_LABELS_PATH: str = os.getenv(
        "VISION_LABELS_PATH", str(APP_DIR / "vision" / "labels.json")
    )
    VISION_IMG_SIZE = (160, 160)  # must match training (see final_model notebook, Config.IMG_SIZE)
    VISION_TOP_K: int = int(os.getenv("VISION_TOP_K", "5"))
    VISION_CONFIDENCE_THRESHOLD: float = float(os.getenv("VISION_CONFIDENCE_THRESHOLD", "0.75"))

    # --- GPS Validation (Layer 2) ---------------------------------------
    GPS_MAX_DISTANCE_METERS: float = float(os.getenv("GPS_MAX_DISTANCE_METERS", "500"))

    # --- Database / Knowledge Base (Layer 3) -----------------------------
    # Defaults to a local SQLite file so the API runs out of the box.
    # For production point this at managed Postgres, e.g.:
    # postgresql+psycopg2://user:pass@host:5432/tourism
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'tourism.db'}"
    )

    # --- LLM (Layer 4) ----------------------------------------------------
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "none")  # openai | gemini | none
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # --- TTS (Layer 5) -----------------------------------------------------
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "none")  # elevenlabs | openai | none
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "")
    OPENAI_TTS_VOICE: str = os.getenv("OPENAI_TTS_VOICE", "alloy")

    # Audio storage: local folder by default; swap for S3/MinIO in production
    AUDIO_CACHE_DIR: str = os.getenv("AUDIO_CACHE_DIR", str(APP_DIR / "storage" / "audio_cache"))
    AUDIO_PUBLIC_BASE_URL: str = os.getenv("AUDIO_PUBLIC_BASE_URL", "/audio")


settings = Settings()
os.makedirs(settings.AUDIO_CACHE_DIR, exist_ok=True)
