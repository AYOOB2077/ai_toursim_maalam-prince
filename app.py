"""
Root entrypoint for running the AI Tourism Backend API from workspace root.
Exposes `app` for ASGI servers (uvicorn, gunicorn, Hugging Face Spaces, etc.).
"""
import os
import sys

# Ensure inner project directory is in python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ai_tourism_api"))

import uvicorn
from ai_tourism_api.app.main import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run("ai_tourism_api.app.main:app", host="0.0.0.0", port=port, reload=True)
