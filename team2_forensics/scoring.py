import json

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, shape

def load_source_corridor(path):
    """
    Load Person A's source corridor from a GeoJSON file.

    Expected format:

    {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [...]
        },
        "properties": {}
    }
    """

    with open(path, "r", encoding="utf-8") as file:
        geojson = json.load(file)

    geometry = shape(geojson["geometry"])

    return geometry

def create_demo_corridor():
    """
    Temporary narrow demo source corridor.

    This approximates the kind of corridor that will eventually
    come from Person A's reverse hindcast.
    """

    coordinates = [
        (74.795, 12.495),
        (74.825, 12.505),
        (74.825, 12.515),
        (74.795, 12.505),
        (74.795, 12.495),
    ]

    return Polygon(coordinates)

def prepare_ais(ais_df):
    """Convert AIS latitude/longitude into GeoDataFrame points."""

    geometry = [
        Point(lon, lat)
        for lon, lat in zip(
            ais_df["longitude"],
            ais_df["latitude"]
        )
    ]

    gdf = gpd.GeoDataFrame(
        ais_df.copy(),
        geometry=geometry,
        crs="EPSG:4326"
    )

    return gdf


def calculate_distance_km(ais_gdf, corridor):
    """
    Calculate approximate distance from each AIS position
    to the source corridor in kilometres.
    """

    # Project to a metric CRS for distance calculations.
    projected = ais_gdf.to_crs("EPSG:32643")
    corridor_projected = gpd.GeoSeries(
        [corridor],
        crs="EPSG:4326"
    ).to_crs("EPSG:32643").iloc[0]

    distances = projected.geometry.distance(corridor_projected)

    return distances / 1000


def calculate_spatial_score(distance_km):
    """Convert distance into a 0-100 spatial score."""

    if distance_km <= 1:
        return 100

    if distance_km >= 20:
        return 0

    return 100 * (1 - (distance_km - 1) / 19)


def calculate_temporal_score(time_gap_minutes):
    """Convert time difference into a 0-100 temporal score."""

    if time_gap_minutes <= 15:
        return 100

    if time_gap_minutes >= 180:
        return 0

    return 100 * (1 - (time_gap_minutes - 15) / 165)


def calculate_track_score(point, corridor):
    """Score whether a vessel position lies inside the corridor."""

    if corridor.contains(point):
        return 100

    return 0


def rank_candidates(
    ais_df,
    corridor,
    detection_time,
    time_window_minutes=180
):
    """
    Rank vessels according to spatial proximity,
    temporal compatibility and corridor consistency.
    """

    ais_gdf = prepare_ais(ais_df)

    detection_time = pd.to_datetime(
        detection_time,
        utc=True
    )

    # Calculate time difference from spill detection.
    ais_gdf["time_gap_minutes"] = (
        ais_gdf["timestamp"] - detection_time
    ).abs().dt.total_seconds() / 60

    # Keep observations within the allowed time window.
    filtered = ais_gdf[
        ais_gdf["time_gap_minutes"] <= time_window_minutes
    ].copy()

    if filtered.empty:
        return []

    # Calculate spatial distance.
    filtered["distance_km"] = calculate_distance_km(
        filtered,
        corridor
    )

    # Calculate individual scores.
    filtered["spatial_score"] = filtered[
        "distance_km"
    ].apply(calculate_spatial_score)

    filtered["temporal_score"] = filtered[
        "time_gap_minutes"
    ].apply(calculate_temporal_score)

    filtered["track_score"] = filtered.geometry.apply(
        lambda point: calculate_track_score(
            point,
            corridor
        )
    )

    # Team-approved initial weighting.
    filtered["relevance_score"] = (
        0.40 * filtered["spatial_score"]
        + 0.35 * filtered["temporal_score"]
        + 0.25 * filtered["track_score"]
    )

    # Find the strongest observation for each vessel.
    best_observations = (
        filtered
        .sort_values("relevance_score", ascending=False)
        .groupby("vessel_id")
        .first()
        .reset_index()
    )

    # Rank vessels.
    best_observations = best_observations.sort_values(
        "relevance_score",
        ascending=False
    )

    candidates = []

    for _, row in best_observations.head(3).iterrows():

        if row["track_score"] == 100:
            reason = (
                "Vessel position intersects the source corridor "
                "with compatible timing"
            )
        else:
            reason = (
                "Close spatial and temporal match to "
                "source corridor"
            )

        candidates.append({
            "vessel_id": row["vessel_id"],
            "relevance_score": round(
                row["relevance_score"]
            ),
            "distance_km": round(
                row["distance_km"],
                2
            ),
            "time_gap_minutes": round(
                row["time_gap_minutes"]
            ),
            "reason": reason
        })

    return candidates


if __name__ == "__main__":

    # Load synthetic AIS.
    ais = pd.read_csv(
        "data/synthetic_ais.csv"
    )

    ais["timestamp"] = pd.to_datetime(
        ais["timestamp"],
        utc=True
    )

    # Temporary demo corridor.
    hindcast_path = "outputs/sample_hindcast.geojson"

    with open(hindcast_path, "r", encoding="utf-8") as file:
        hindcast = json.load(file)

    corridor = shape(
        hindcast["source_corridor"]["geometry"]
    )

    # Demo incident time.
    detection_time = "2026-08-30T12:00:00Z"

    candidates = rank_candidates(
        ais,
        corridor,
        detection_time
    )

    print("\nTop candidate vessels:\n")

    for candidate in candidates:
        print(candidate)