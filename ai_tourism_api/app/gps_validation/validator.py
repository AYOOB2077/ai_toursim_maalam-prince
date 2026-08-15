"""
LAYER 2 — GPS VALIDATION
========================
Cross-checks the Vision layer's candidate landmarks against the user's GPS
coordinates and picks the candidate whose known location is closest.
Deterministic, sub-millisecond, no external service required.
"""
import math
from typing import List, Optional, Tuple

from app.config import settings
from app.database.models import Landmark


def haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two (lat, lng) points, in meters."""
    R = 6_371_000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def validate_candidates(
    candidates: List[dict],
    user_lat: Optional[float],
    user_lng: Optional[float],
    all_landmarks: List[Landmark],
    max_distance_m: float = None,
) -> Tuple[Optional[Landmark], bool]:
    """
    Picks the best landmark among the vision candidates.

    Returns (landmark_or_None, validated_by_gps: bool).
    - If GPS is unavailable, falls back to the top vision candidate by name match.
    - If GPS is available, prefers the candidate whose registered coordinates
      are closest to the user and within max_distance_m.
    """
    max_distance_m = max_distance_m or settings.GPS_MAX_DISTANCE_METERS
    by_slug = {lm.slug: lm for lm in all_landmarks}

    ranked_candidate_landmarks = [
        (c, by_slug[c["label"]]) for c in candidates if c["label"] in by_slug
    ]

    if not ranked_candidate_landmarks:
        return None, False

    if user_lat is None or user_lng is None:
        # No GPS: trust the vision model's top-ranked candidate.
        return ranked_candidate_landmarks[0][1], False

    best_landmark = None
    best_distance = float("inf")
    for _candidate, landmark in ranked_candidate_landmarks:
        dist = haversine_meters(user_lat, user_lng, landmark.latitude, landmark.longitude)
        if dist < best_distance:
            best_distance = dist
            best_landmark = landmark

    if best_landmark is not None and best_distance <= max_distance_m:
        return best_landmark, True

    # GPS didn't confirm any candidate within range -> fall back to vision's top pick.
    return ranked_candidate_landmarks[0][1], False
