"""
Root entrypoint for running the AI Tourism Backend API.
Exposes `app` for ASGI servers (uvicorn, gunicorn, Hugging Face Spaces, etc.)
and enables direct execution via `python app.py`.
"""
import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
