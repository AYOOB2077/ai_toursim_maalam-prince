"""
LAYER 3 — KNOWLEDGE DATABASE
============================
Single source of truth for verified, curated landmark content. The Vision
layer only ever returns a class label (e.g. "landmark_1") — this table maps
that label to real-world facts, coordinates, and multilingual summaries.
"""
from sqlalchemy import Column, Float, Integer, String, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Landmark(Base):
    __tablename__ = "landmarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String, unique=True, index=True, nullable=False)  # must match vision/labels.json values
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    era = Column(String, nullable=True)
    history = Column(String, nullable=True)
    fun_facts = Column(JSON, default=list)          # List[str]
    summaries = Column(JSON, default=dict)          # Dict[lang_code, str]

    def to_facts_dict(self) -> dict:
        return {
            "slug": self.slug,
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "era": self.era,
            "history": self.history,
            "fun_facts": self.fun_facts or [],
            "summaries": self.summaries or {},
        }
