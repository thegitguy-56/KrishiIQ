"""
Geospatial pest/disease spread risk model.

Estimates spread risk between neighboring farms using proximity (haversine
distance), matching crop type, and wind direction as a rule-based heuristic.

NOTE ON NAMING: this module was previously called gnn_model.py and its
docstring described it as "GNN-based" (Graph Neural Network). That was
inaccurate — there is no trained neural network here, no torch-geometric
usage, and no learned parameters. It's a deterministic formula with
hand-chosen weights. Renamed and re-documented for accuracy; the underlying
logic is unchanged (aside from the crop-matching fix noted below).

Building a genuine GNN for this would require historical, labeled
farm-to-farm disease-spread data to train on, which isn't available here —
a model "trained" without that would just be fitting noise while looking
more sophisticated than it is. This heuristic is honest about being a
heuristic, which is preferable for a system real farmers might rely on.
"""
import math
from typing import List, Dict, Optional


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def compute_spread_risk(
    source_farm: Dict,
    target_farm: Dict,
    disease_name: str,
    wind_direction_deg: Optional[float] = None,
) -> float:
    """Returns a 0-1 risk score for disease spread from source to target farm."""
    dist_km = haversine_km(
        source_farm["latitude"], source_farm["longitude"],
        target_farm["latitude"], target_farm["longitude"],
    )

    if dist_km > 10:
        return 0.0

    proximity_score = max(0, 1 - (dist_km / 10))

    # Only apply the same-crop multiplier when both farms actually have a
    # known, non-null crop that matches. Previously this compared None == None
    # (always True when crop data wasn't populated by the caller), so the
    # multiplier silently fired for every farm pair regardless of what was
    # actually planted. Fixed here; the caller must now pass real crop values
    # for this to have any effect (see dashboard.py's pest-spread-risk route).
    source_crop = source_farm.get("crop")
    target_crop = target_farm.get("crop")
    crop_match = 1.5 if (source_crop and target_crop and source_crop == target_crop) else 1.0

    wind_score = 1.0
    if wind_direction_deg is not None and dist_km > 0:
        bearing = math.degrees(math.atan2(
            target_farm["longitude"] - source_farm["longitude"],
            target_farm["latitude"] - source_farm["latitude"],
        )) % 360
        angle_diff = abs(bearing - wind_direction_deg)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        wind_score = 1 + (0.5 * (1 - angle_diff / 180))

    risk = min(1.0, proximity_score * crop_match * wind_score * 0.6)
    return round(risk, 3)


def build_risk_graph(farms: List[Dict], infected_farm_ids: List[str], wind_direction_deg: Optional[float] = None) -> List[Dict]:
    """
    Returns list of at-risk farms with their spread risk scores.
    Each farm dict needs: id, latitude, longitude, crop
    """
    infected = [f for f in farms if str(f["id"]) in infected_farm_ids]
    healthy = [f for f in farms if str(f["id"]) not in infected_farm_ids]

    results = []
    for target in healthy:
        max_risk = 0.0
        source_farm_id = None
        for source in infected:
            risk = compute_spread_risk(source, target, "unknown", wind_direction_deg)
            if risk > max_risk:
                max_risk = risk
                source_farm_id = str(source["id"])
        if max_risk > 0.1:
            results.append({
                "farm_id": str(target["id"]),
                "spread_risk": max_risk,
                "risk_level": "high" if max_risk > 0.7 else "medium" if max_risk > 0.4 else "low",
                "nearest_infected_farm_id": source_farm_id,
            })

    return sorted(results, key=lambda x: x["spread_risk"], reverse=True)