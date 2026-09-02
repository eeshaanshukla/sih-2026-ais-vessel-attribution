import json
from pathlib import Path

import pandas as pd
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from team2_forensics.scoring import rank_candidates


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

AIS_PATH = BASE_DIR / "data" / "integration_ais.csv"

FALLBACK_HINDCAST_PATH = (
    BASE_DIR / "outputs" / "person_a_hindcast.geojson"
)

PERSON_A_HINDCAST_URL = (
    "https://namespace-reflect-lol-glossary.trycloudflare.com/hindcast"
)


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------

app = FastAPI(
    title="Team 2 Vessel Attribution API",
    description="Ranks candidate vessels using AIS and hindcast source corridor.",
    version="1.0.0"
)


# ---------------------------------------------------------
# Request model
# ---------------------------------------------------------

class AttributeRequest(BaseModel):
    incident_id: str
    detection_time: str
    centroid: list[float]
    spill_geojson: dict


# ---------------------------------------------------------
# Helper: call Person A /hindcast
# ---------------------------------------------------------

def get_hindcast(request_data):
    """
    Call Person A's /hindcast API.

    If Person A's API is temporarily unavailable,
    use the locally saved hindcast as a fallback.
    """

    hindcast_request = {
        "incident_id": request_data.incident_id,
        "centroid": request_data.centroid,
        "detection_time": request_data.detection_time,
        "spill_geojson": request_data.spill_geojson
    }

    try:
        response = requests.post(
            PERSON_A_HINDCAST_URL,
            json=hindcast_request,
            timeout=180
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as error:

        print(
            f"Person A /hindcast unavailable: {error}"
        )

        if not FALLBACK_HINDCAST_PATH.exists():
            raise HTTPException(
                status_code=503,
                detail="Hindcast service unavailable and no fallback is available."
            )

        print("Using local hindcast fallback.")

        with open(
            FALLBACK_HINDCAST_PATH,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)


# ---------------------------------------------------------
# API endpoint
# ---------------------------------------------------------

@app.post("/attribute")
def attribute(request_data: AttributeRequest):

    # 1. Get hindcast from Person A.
    hindcast = get_hindcast(request_data)

    # 2. Validate source corridor.
    if "source_corridor" not in hindcast:
        raise HTTPException(
            status_code=502,
            detail="Hindcast response does not contain source_corridor."
        )

    source_corridor = hindcast["source_corridor"]

    if "geometry" not in source_corridor:
        raise HTTPException(
            status_code=502,
            detail="source_corridor does not contain geometry."
        )

    # 3. Convert corridor geometry to Shapely.
    from shapely.geometry import shape

    corridor = shape(
        source_corridor["geometry"]
    )

    if corridor.is_empty:
        raise HTTPException(
            status_code=502,
            detail="Hindcast source corridor is empty."
        )

    # 4. Load AIS dataset.
    if not AIS_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail="AIS dataset not found."
        )

    ais = pd.read_csv(AIS_PATH)

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
        raise HTTPException(
            status_code=500,
            detail=(
                "AIS data is missing required columns: "
                f"{sorted(missing_columns)}"
            )
        )

    # 5. Convert timestamps.
    ais["timestamp"] = pd.to_datetime(
        ais["timestamp"],
        utc=True,
        errors="coerce"
    )

    if ais["timestamp"].isna().any():
        raise HTTPException(
            status_code=500,
            detail="AIS data contains invalid timestamps."
        )

    # 6. Rank candidate vessels.
    candidates = rank_candidates(
        ais_df=ais,
        corridor=corridor,
        detection_time=request_data.detection_time
    )

    # 7. Return Team 2 /attribute contract.
    return {
        "incident_id": request_data.incident_id,
        "candidate_vessels": candidates
    }


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "running",
        "service": "Team 2 Vessel Attribution API"
    }