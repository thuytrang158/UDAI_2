"""
Geographic Clustering Tool.
Partitions selected places into days based on latitude/longitude proximity.
"""
import math
from typing import List, Dict, Any


def group_places_by_days(
    places: List[Dict[str, Any]],
    num_days: int
) -> List[List[Dict[str, Any]]]:
    """
    Distributes places across the requested number of days.
    - Separates far-distance outliers (>30 km from the selected-places centroid).
    - Groups geographically close spots together to minimize driving.
    """
    if not places:
        return [[] for _ in range(num_days)]

    located = [p for p in places if p.get("latitude") is not None and p.get("longitude") is not None]
    if not located:
        buckets = [[] for _ in range(num_days)]
        for index, place in enumerate(places):
            buckets[index % num_days].append(place)
        return buckets
    center_lat = sum(float(p["latitude"]) for p in located) / len(located)
    center_lon = sum(float(p["longitude"]) for p in located) / len(located)
    outliers = []
    central_places = []

    for p in places:
        if p.get("latitude") is None or p.get("longitude") is None:
            central_places.append(p)
            continue
        # Approximate local distance; the longitude adjustment scales by latitude.
        lat_delta = (float(p["latitude"]) - center_lat) * 111.0
        lon_delta = (float(p["longitude"]) - center_lon) * 111.0 * math.cos(math.radians(center_lat))
        if (lat_delta ** 2 + lon_delta ** 2) ** 0.5 > 30:
            outliers.append(p)
        else:
            central_places.append(p)

    # Distribute into daily buckets
    daily_buckets: List[List[Dict[str, Any]]] = [[] for _ in range(num_days)]

    # 1. Assign outlier / big excursion to Day 1 (early sunrise trek) or Day 2
    bucket_idx = 0
    for out in outliers:
        daily_buckets[bucket_idx % num_days].append(out)
        bucket_idx += 1

    # 2. Sort central places by latitude so adjacent places stay together
    central_places.sort(key=lambda p: p.get("latitude") if p.get("latitude") is not None else center_lat)

    # 3. Fill the days evenly
    for place in central_places:
        # Find the day bucket with the fewest places
        min_bucket = min(daily_buckets, key=lambda b: len(b))
        min_bucket.append(place)

    return daily_buckets
