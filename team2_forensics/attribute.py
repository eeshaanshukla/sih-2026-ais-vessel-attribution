import json

import pandas as pd
from shapely.geometry import shape

from team2_forensics.scoring import rank_candidates


def run_attribution(
    incident_id,
    ais_path,
    hindcast_path,
    detection_time
):
    """
    Run vessel attribution using AIS data and a hindcast
    source corridor.

    Returns the exact /attribute response schema.
    """

    # Load AIS data.
    ais = pd.read_csv(ais_path)

    ais["timestamp"] = pd.to_datetime(
        ais["timestamp"],
        utc=True
    )

    # Load Person A's hindcast output.
    with open(hindcast_path, "r", encoding="utf-8") as file:
        hindcast = json.load(file)

    # Extract the source corridor from the shared GeoJSON contract.
    corridor = shape(
        hindcast["source_corridor"]["geometry"]
    )

    # Rank candidate vessels.
    candidates = rank_candidates(
        ais_df=ais,
        corridor=corridor,
        detection_time=detection_time
    )

    # Return exact shared /attribute schema.
    return {
        "incident_id": incident_id,
        "candidate_vessels": candidates
    }


if __name__ == "__main__":

    result = run_attribution(
        incident_id="INC001",
        ais_path="data/synthetic_ais.csv",
        hindcast_path="outputs/sample_hindcast.geojson",
        detection_time="2026-08-30T12:00:00Z"
    )

    print(json.dumps(result, indent=2))