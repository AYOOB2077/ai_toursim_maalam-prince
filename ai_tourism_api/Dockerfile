FROM python:3.11-slim

WORKDIR /srv

# System deps for Pillow / TensorFlow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev zlib1g-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Seed the knowledge base then start the API.
CMD ["sh", "-c", "python -m app.database.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
