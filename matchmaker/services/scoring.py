from __future__ import annotations

import math
from typing import Dict, Iterable, List

from .lastfm import artist_identifier


def build_vector(top_artists_payload: Iterable[Dict]) -> Dict[str, float]:
    vector: Dict[str, float] = {}
    for artist in top_artists_payload:
        plays = int(artist.get("playcount", 0))
        weight = math.log(plays + 1)
        if weight <= 0:
            continue
        key = artist_identifier(artist)
        vector[key] = weight
    return vector


def _l2_norm(vec: Dict[str, float]) -> float:
    return math.sqrt(sum(v * v for v in vec.values()))


def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    dot = sum(vec_a.get(k, 0) * vec_b.get(k, 0) for k in vec_a.keys())
    norm_a = _l2_norm(vec_a)
    norm_b = _l2_norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _artist_name_map(payloads: List[Dict]) -> Dict[str, str]:
    mapping = {}
    for artist in payloads:
        key = artist_identifier(artist)
        mapping[key] = artist.get("name") or key
    return mapping


def compute_match(
    user_a_payloads: Dict[str, List[Dict]], user_b_payloads: Dict[str, List[Dict]]
) -> Dict:
    periods = ["3month", "12month", "overall"]
    vectors_a = {p: build_vector(user_a_payloads.get(p, [])) for p in periods}
    vectors_b = {p: build_vector(user_b_payloads.get(p, [])) for p in periods}

    scores = {p: round(cosine_similarity(vectors_a[p], vectors_b[p]), 4) for p in periods}
    final_score = (
        0.55 * scores["3month"] + 0.30 * scores["12month"] + 0.15 * scores["overall"]
    )

    primary_period = "overall"
    source_period = primary_period if user_a_payloads.get(primary_period) else "12month"
    if not user_a_payloads.get(source_period):
        source_period = "3month"

    name_map_a = _artist_name_map(user_a_payloads.get(source_period, []))
    name_map_b = _artist_name_map(user_b_payloads.get(source_period, []))

    vec_a = vectors_a.get(source_period, {})
    vec_b = vectors_b.get(source_period, {})

    overlap = []
    for key in set(vec_a.keys()).intersection(vec_b.keys()):
        overlap.append(
            {
                "artist": name_map_a.get(key) or name_map_b.get(key) or key,
                "a_weight": vec_a.get(key, 0.0),
                "b_weight": vec_b.get(key, 0.0),
                "combined": vec_a.get(key, 0.0) + vec_b.get(key, 0.0),
            }
        )
    overlap.sort(key=lambda x: x["combined"], reverse=True)
    overlap = overlap[:10]

    def missing_recs(source_vec: Dict[str, float], target_vec: Dict[str, float], name_map: Dict):
        recs = []
        for key, weight in source_vec.items():
            if key not in target_vec:
                recs.append({"artist": name_map.get(key, key), "weight": weight})
        recs.sort(key=lambda x: x["weight"], reverse=True)
        return recs[:10]

    recs_for_a = missing_recs(vec_b, vec_a, name_map_b)
    recs_for_b = missing_recs(vec_a, vec_b, name_map_a)

    return {
        "scores": scores,
        "final_score": round(final_score * 100, 1),
        "overlap": overlap,
        "recs_for_a": recs_for_a,
        "recs_for_b": recs_for_b,
    }
