# AI Tourism — Backend API (6-Layer AI Pipeline)

This is **only the API**, built from `AI_Tourism_Architecture.docx` and your
trained model `best_tourism_model.keras`. It does not include a mobile app —
your existing app just calls this API's `POST /recognize` endpoint over
HTTPS, from the cloud or from the phone.

The architecture document defines 7 layers; layer 1 (the mobile app) is
yours already, so this folder implements the remaining **six**:

| # | Layer | Folder | What it does |
|---|-------|--------|---------------|
| 1 | Vision Model | `app/vision/` | Loads your trained `best_tourism_model.keras` and predicts candidate landmarks from a photo |
| 2 | GPS Validation | `app/gps_validation/` | Cross-checks candidates against real coordinates (haversine distance) to resolve ambiguity |
| 3 | Knowledge Database | `app/database/` | Stores verified facts per landmark (SQLite by default, Postgres-ready) |
| 4 | LLM Narrator | `app/llm/` | Rewrites the verified facts into a story (OpenAI / Gemini / offline template fallback) |
| 5 | Text-to-Speech | `app/tts/` | Converts the story into an MP3 (ElevenLabs / OpenAI TTS / disabled fallback) |
| 6 | Backend API | `app/main.py`, `app/orchestrator.py` | FastAPI service that chains 1→5 and is what your app actually calls |

## Your trained model

`app/vision/best_tourism_model.keras` is the exact file you uploaded:
`MobileNetV3Large` backbone → `GlobalAveragePooling2D` → `Dropout` →
`Dense(256, relu)` → `BatchNormalization` → `Dropout` → `Dense(4, softmax)`,
input size `160×160×3`. It outputs **4 classes**.

`app/vision/labels.json` now has your real classes (`castel`, `flag`,
`patra`, `wady ram`), and `app/database/landmarks_seed.json` has a matching
entry for each — Aqaba Castle, the Aqaba Flagpole (Great Arab Revolt
Flagpole), Petra, and Wadi Rum, with approximate coordinates and starter
history text.

**Before going live, double-check `landmarks_seed.json`** — I filled it in
from general knowledge, not from your training data, so:
- Confirm "castel" is actually Aqaba Castle and not a different fort your
  photos were trained on.
- Verify the coordinates and history text, and expand the `fun_facts` and
  `summaries` fields with anything you want the narrator to be able to use.
- Each entry is marked `VERIFY AND EXPAND` in the `history` field as a
  reminder — remove that note once you've checked it.

## Running locally

```bash
cp .env.example .env
pip install -r requirements.txt
python -m app.database.seed        # loads landmarks_seed.json into the DB
uvicorn app.main:app --reload
```

Then test it:

```bash
curl -X POST http://localhost:8000/recognize \
  -F "image=@/path/to/photo.jpg" \
  -F "latitude=31.9539" \
  -F "longitude=35.9106" \
  -F "language=en"
```

## Running with Docker (recommended for cloud deployment)

```bash
docker compose up --build
```

This starts the API plus a Postgres/PostGIS database, matching the
architecture doc's recommended stack.

## Connecting from your app (cloud or phone)

Your app just needs to call:

```
POST https://your-server/recognize
Content-Type: multipart/form-data
  image:      <jpeg/png file>
  latitude:   <float, optional>
  longitude:  <float, optional>
  language:   <e.g. "en", "ar">
Header: X-API-Key: <your API_KEY, if you set one in .env>
```

Response:

```json
{
  "landmark_id": "landmark_1",
  "landmark_name": "...",
  "confidence": 0.94,
  "candidates": [{"label": "landmark_1", "confidence": 0.94}, ...],
  "story": "...",
  "audio_url": "/audio/<hash>.mp3",
  "facts": {...},
  "validated_by_gps": true
}
```

If `audio_url` is `null`, no TTS provider is configured yet (see below) —
the app can still display/read `story` as text.

## Enabling LLM storytelling and TTS (optional)

By default `LLM_PROVIDER=none` and `TTS_PROVIDER=none`, so the API runs
fully offline with a simple templated story and no audio. To turn on real
storytelling and voice, set in `.env`:

```
LLM_PROVIDER=openai        # or gemini
OPENAI_API_KEY=sk-...

TTS_PROVIDER=elevenlabs    # or openai
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
```

## Deploying to the cloud

The `Dockerfile` builds a self-contained image — push it to any container
host (AWS ECS/Fargate, GCP Cloud Run, Azure Container Apps, Railway,
Fly.io, etc.), point `DATABASE_URL` at a managed Postgres instance, and set
`AUDIO_CACHE_DIR` to a mounted volume or swap `app/tts/speech.py`'s
`_url_for` for a real S3/CDN URL.

## Project layout

```
ai_tourism_api/
├── app/
│   ├── main.py            # Layer 6: FastAPI entrypoint (POST /recognize)
│   ├── orchestrator.py     # chains layers 1→5 in order
│   ├── config.py           # all environment variables
│   ├── schemas.py          # request/response models
│   ├── vision/              # Layer 1
│   │   ├── model.py
│   │   ├── best_tourism_model.keras
│   │   └── labels.json      # <-- EDIT ME
│   ├── gps_validation/      # Layer 2
│   │   └── validator.py
│   ├── database/            # Layer 3
│   │   ├── models.py
│   │   ├── session.py
│   │   ├── seed.py
│   │   └── landmarks_seed.json  # <-- EDIT ME
│   ├── llm/                 # Layer 4
│   │   └── narrator.py
│   ├── tts/                 # Layer 5
│   │   └── speech.py
│   └── storage/audio_cache/ # local MP3 cache (swap for S3/MinIO in prod)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```
