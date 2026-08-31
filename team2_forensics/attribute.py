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

    required_columns = {
        "vessel_id",
        "timestamp",
        "latitude",
        "longitude",
        "speed",
        "heading"
    }

    missing_columns = required_columns - set(ais.columns)

    if missing_columns:
        raise ValueError(
            f"AIS data is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    ais["timestamp"] = pd.to_datetime(
        ais["timestamp"],
        utc=True,
        errors="coerce"
    )

    if ais["timestamp"].isna().any():
        raise ValueError(
            "AIS data contains invalid timestamps."
        )

    # Load Person A's hindcast output.
    with open(
        hindcast_path,
        "r",
        encoding="utf-8"
    ) as file:
        hindcast = json.load(file)

    # Validate the shared /hindcast contract.
    if "source_corridor" not in hindcast:
        raise ValueError(
            "Hindcast output does not contain "
            "'source_corridor'."
        )

    if "geometry" not in hindcast["source_corridor"]:
        raise ValueError(
            "source_corridor does not contain "
            "'geometry'."
        )

    # Extract the source corridor from the shared GeoJSON contract.
    corridor = shape(
        hindcast["source_corridor"]["geometry"]
    )

    if corridor.is_empty:
        raise ValueError(
            "source_corridor geometry is empty."
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

    print(
        json.dumps(
            result,
            indent=2
        )
    )