# Project Structure Tree

```text
ai_tourism_api/
├── .vscode/
│   └── settings.json                 # Workspace & Python interpreter configuration
├── pyproject.toml                    # Root linter & package configuration
├── pyrightconfig.json                # Outer Pyright type-checker config
├── app.py                            # Outer entrypoint for running backend from workspace root
└── ai_tourism_api/                   # 📁 Main Application Directory
    ├── .env                          # Active environment variables & API keys
    ├── .env.example                  # Template environment variables
    ├── .venv/                        # Virtual Environment directory
    ├── app.py                        # Primary entrypoint (python app.py)
    ├── Dockerfile                    # Container deployment file
    ├── docker-compose.yml            # Docker orchestration configuration
    ├── pyproject.toml                # Inner project config
    ├── pyrightconfig.json            # Inner Pyright config
    ├── README.md                     # Documentation & setup guide
    ├── requirements.txt              # Python package dependencies
    ├── tourism.db                    # Local SQLite database file
    └── app/                          # 🧠 Backend Core Package
        ├── __init__.py
        ├── config.py                 # Central configuration & settings
        ├── main.py                   # FastAPI app, endpoints & lifespan handler
        ├── orchestrator.py            # 5-stage AI pipeline orchestrator
        ├── schemas.py                # Pydantic request/response models
        ├── database/                 # 🗄️ Layer 3 — Knowledge Database
        │   ├── __init__.py
        │   ├── landmarks_seed.json    # Curated landmark seed JSON
        │   ├── models.py             # SQLAlchemy Landmark DB schema
        │   ├── seed.py               # Database seed script (python -m app.database.seed)
        │   └── session.py            # Database connection & session setup
        ├── gps_validation/           # 📍 Layer 2 — Spatial Verification
        │   ├── __init__.py
        │   └── validator.py          # Haversine distance calculator & GPS filter
        ├── llm/                      # 📖 Layer 4 — Multilingual Storyteller
        │   ├── __init__.py
        │   └── narrator.py           # OpenAI / Gemini / Fallback narration engine
        ├── storage/                  # 💾 Audio storage directory
        │   └── audio_cache/          # Cached MP3 audio narrations
        ├── tts/                      # 🔊 Layer 5 — Audio Narration (Text-to-Speech)
        │   ├── __init__.py
        │   └── speech.py             # gTTS / ElevenLabs / OpenAI speech synthesizer
        └── vision/                   # 👁️ Layer 1 — Image Recognition
            ├── __init__.py
            ├── best_tourism_model.keras # Trained MobileNetV3 Keras model
            ├── labels.json           # Class label mapping file
            └── model.py              # VisionService loader & Hugging Face downloader
```

## Module Descriptions

- **`app/main.py`**: FastAPI application entry point, routes, CORS middleware, and lifespan event handlers.
- **`app/orchestrator.py`**: 5-stage AI pipeline coordinator (Vision → GPS → Knowledge DB → LLM → TTS).
- **`app/vision/model.py`**: MobileNetV3 model loader with Hugging Face Hub integration and fallback.
- **`app/gps_validation/validator.py`**: Distance calculation between user GPS coordinates and target landmarks.
- **`app/database/`**: Knowledge base storing landmark facts, coordinates, and multilingual summaries.
- **`app/llm/narrator.py`**: Generates storytelling scripts using OpenAI GPT-4o-mini, Gemini, or local fallback.
- **`app/tts/speech.py`**: Synthesizes audio narration into MP3s using gTTS, ElevenLabs, or OpenAI TTS.
