import json

import pandas as pd
from shapely.geometry import shape

from team2_forensics.scoring import rank_candidates


def test_candidate_ranking():
    ais = pd.read_csv("data/synthetic_ais.csv")

    ais["timestamp"] = pd.to_datetime(
        ais["timestamp"],
        utc=True
    )

    with open(
        "outputs/sample_hindcast.geojson",
        "r",
        encoding="utf-8"
    ) as file:
        hindcast = json.load(file)

    corridor = shape(
        hindcast["source_corridor"]["geometry"]
    )

    candidates = rank_candidates(
        ais_df=ais,
        corridor=corridor,
        detection_time="2026-08-30T12:00:00Z"
    )

    assert len(candidates) == 3

    for candidate in candidates:
        assert "vessel_id" in candidate
        assert "relevance_score" in candidate
        assert "distance_km" in candidate
        assert "time_gap_minutes" in candidate
        assert "reason" in candidate

        assert 0 <= candidate["relevance_score"] <= 100
        assert candidate["distance_km"] >= 0
        assert candidate["time_gap_minutes"] >= 0


def test_no_vessels_in_time_window():
    ais = pd.read_csv("data/synthetic_ais.csv")

    ais["timestamp"] = pd.to_datetime(
        ais["timestamp"],
        utc=True
    )

    with open(
        "outputs/sample_hindcast.geojson",
        "r",
        encoding="utf-8"
    ) as file:
        hindcast = json.load(file)

    corridor = shape(
        hindcast["source_corridor"]["geometry"]
    )

    candidates = rank_candidates(
        ais_df=ais,
        corridor=corridor,
        detection_time="2026-08-31T12:00:00Z",
        time_window_minutes=30
    )

    assert candidates == []


def test_only_top_three_vessels_returned():
    ais = pd.read_csv("data/synthetic_ais.csv")

    ais["timestamp"] = pd.to_datetime(
        ais["timestamp"],
        utc=True
    )

    with open(
        "outputs/sample_hindcast.geojson",
        "r",
        encoding="utf-8"
    ) as file:
        hindcast = json.load(file)

    corridor = shape(
        hindcast["source_corridor"]["geometry"]
    )

    candidates = rank_candidates(
        ais_df=ais,
        corridor=corridor,
        detection_time="2026-08-30T12:00:00Z"
    )

    assert len(candidates) <= 3


def test_one_best_observation_per_vessel():
    ais = pd.read_csv("data/synthetic_ais.csv")

    ais["timestamp"] = pd.to_datetime(
        ais["timestamp"],
        utc=True
    )

    with open(
        "outputs/sample_hindcast.geojson",
        "r",
        encoding="utf-8"
    ) as file:
        hindcast = json.load(file)

    corridor = shape(
        hindcast["source_corridor"]["geometry"]
    )

    candidates = rank_candidates(
        ais_df=ais,
        corridor=corridor,
        detection_time="2026-08-30T12:00:00Z"
    )

    vessel_ids = [
        candidate["vessel_id"]
        for candidate in candidates
    ]

    assert len(vessel_ids) == len(set(vessel_ids))
def test_corridor_boundary_counts_as_inside():
    ais = pd.DataFrame([
        {
            "vessel_id": "BOUNDARY_VESSEL",
            "timestamp": "2026-08-30T12:00:00Z",
            "latitude": 12.495,
            "longitude": 74.795,
            "speed": 10.0,
            "heading": 90.0
        }
    ])

    ais["timestamp"] = pd.to_datetime(
        ais["timestamp"],
        utc=True
    )

    with open(
        "outputs/sample_hindcast.geojson",
        "r",
        encoding="utf-8"
    ) as file:
        hindcast = json.load(file)

    corridor = shape(
        hindcast["source_corridor"]["geometry"]
    )

    candidates = rank_candidates(
        ais_df=ais,
        corridor=corridor,
        detection_time="2026-08-30T12:00:00Z"
    )

    assert len(candidates) == 1
    assert candidates[0]["vessel_id"] == "BOUNDARY_VESSEL"
    assert candidates[0]["relevance_score"] == 100