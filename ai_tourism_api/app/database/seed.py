"""
Loads app/database/landmarks_seed.json into the knowledge_base table.
Run with:  python -m app.database.seed
Re-running is safe — it upserts by slug.
"""
import json
from pathlib import Path

from app.database.models import Landmark
from app.database.session import SessionLocal, init_db

SEED_PATH = Path(__file__).parent / "landmarks_seed.json"


def run():
    init_db()
    with open(SEED_PATH, "r") as f:
        records = json.load(f)

    db = SessionLocal()
    try:
        for rec in records:
            existing = db.query(Landmark).filter_by(slug=rec["slug"]).first()
            if existing:
                for key, value in rec.items():
                    setattr(existing, key, value)
            else:
                db.add(Landmark(**rec))
        db.commit()
        print(f"Seeded {len(records)} landmark(s) into the knowledge base.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
