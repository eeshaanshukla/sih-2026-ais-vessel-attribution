# SIH 2026 — AIS-Based Vessel Attribution

> **Team 2 — Spill Forensics & Vessel Attribution**

A geospatial vessel-attribution module for correlating oil-spill source corridors with AIS vessel observations and ranking candidate vessels based on spatial and temporal relevance.

---

## Table of Contents

* [Overview](#overview)
* [Problem Context](#problem-context)
* [System Role](#system-role)
* [Team 2 Workflow](#team-2-workflow)
* [Key Features](#key-features)
* [Technology Stack](#technology-stack)
* [Repository Structure](#repository-structure)
* [AIS Data](#ais-data)
* [Source Corridor & Hindcast](#source-corridor--hindcast)
* [Vessel Ranking](#vessel-ranking)
* [API](#api)
* [API Request](#api-request)
* [API Response](#api-response)
* [Running Locally](#running-locally)
* [Testing](#testing)
* [Example Workflow](#example-workflow)
* [Design Principles](#design-principles)
* [Limitations](#limitations)
* [Future Improvements](#future-improvements)
* [Team 2 Responsibilities](#team-2-responsibilities)

---

## Overview

This repository contains the **Team 2 Spill Forensics & Vessel Attribution** module developed for **Smart India Hackathon 2026**.

The module helps investigate the possible origin of an oil spill by combining:

* Oil-spill detection information
* Reverse ocean hindcast results
* Probable source corridors
* AIS vessel observations
* Spatial proximity
* Temporal proximity
* Vessel track/corridor consistency

The system produces a ranked list of **candidate vessels** associated with the inferred source corridor.

The output is intended as an **investigative decision-support result**, not as definitive proof of responsibility.

---

## Problem Context

Oil spills detected at sea can be difficult to trace back to their possible source.

Satellite imagery can identify a spill, but determining which vessel may have been associated with the incident requires correlating the spill with:

1. The time at which the spill was detected.
2. The estimated movement of the spilled material.
3. The probable source region.
4. Historical vessel positions and movements.

This module addresses the vessel-correlation part of that workflow.

---

## System Role

The broader project combines satellite-based spill detection, ocean modelling, AIS correlation, and environmental analysis.

```text
                    Satellite Imagery
                           │
                           ▼
                ┌─────────────────────┐
                │   Spill Detection   │
                │      Team 1         │
                └──────────┬──────────┘
                           │
                 Spill polygon
                 Centroid + Time
                           │
                           ▼
                ┌─────────────────────┐
                │   Team 2            │
                │ Spill Forensics     │
                │                     │
                │ Reverse Hindcast    │
                │ Source Corridor     │
                │ AIS Correlation     │
                │ Vessel Ranking      │
                └──────────┬──────────┘
                           │
                           ▼
                Ranked Candidate Vessels
                           │
                           ▼
                ┌─────────────────────┐
                │   Team 3            │
                │ Integration &       │
                │ Environmental       │
                │ Analysis             │
                └─────────────────────┘
```

---

## Team 2 Workflow

The Team 2 attribution pipeline follows this process:

```text
Spill Incident
     │
     ├── Incident ID
     ├── Detection Time
     ├── Spill Centroid
     └── Spill GeoJSON
             │
             ▼
       Reverse Hindcast
             │
             ▼
      Source Corridor
             │
             ▼
       AIS Observations
             │
             ▼
   Temporal Filtering
             │
             ▼
   Spatial Distance Analysis
             │
             ▼
     Track/Corridor Check
             │
             ▼
     Relevance Scoring
             │
             ▼
    Ranked Candidate Vessels
```

---

## Key Features

### Reverse Hindcast

Uses spill information to estimate a probable backward trajectory of the spilled material.

### Source Corridor Generation

Represents the probable source region as a geospatial corridor derived from the hindcast trajectory.

### AIS Correlation

Correlates vessel observations with the inferred source corridor.

### Temporal Matching

Filters AIS observations according to their time difference from the spill detection event.

### Spatial Matching

Calculates the distance between vessel observations and the inferred source corridor using projected geospatial coordinates.

### Explainable Ranking

Combines spatial, temporal, and corridor consistency factors into a transparent relevance score.

### API Integration

Provides a FastAPI `/attribute` endpoint that can be consumed by the rest of the project.

### Fallback Handling

Uses a local hindcast output when the external hindcast service is unavailable.

---

## Technology Stack

| Technology          | Purpose                                        |
| ------------------- | ---------------------------------------------- |
| Python 3.11         | Core implementation                            |
| FastAPI             | REST API                                       |
| Pandas              | AIS data processing                            |
| GeoPandas           | Geospatial data processing                     |
| Shapely             | Geometry operations                            |
| PyProj              | Coordinate projection and distance calculation |
| OpenDrift / OpenOil | Ocean drift and hindcast modelling             |
| Requests            | Hindcast service communication                 |
| Pytest              | Automated testing                              |
| GeoJSON             | Geospatial API exchange format                 |
| Git / GitHub        | Version control                                |

---

## Repository Structure

```text
SIH-Team2/
│
├── backend/
│   └── main.py
│
├── data/
│   ├── synthetic_ais.csv
│   └── integration_ais.csv
│
├── outputs/
│   ├── sample_hindcast.geojson
│   ├── sample_vessels.geojson
│   └── person_a_hindcast.geojson
│
├── team2_forensics/
│   ├── __init__.py
│   ├── ais.py
│   ├── attribute.py
│   └── scoring.py
│
├── tests/
│   └── test_attribution.py
│
├── requirements.txt
└── README.md
```

---

## AIS Data

AIS observations contain the following fields:

```text
vessel_id
timestamp
latitude
longitude
speed
heading
```

Example:

```csv
vessel_id,timestamp,latitude,longitude,speed,heading
VESSEL_A,2026-09-01T20:30:00Z,25.3220,54.4880,12,90
```

The project includes sample/integration AIS data for demonstrating the vessel-attribution workflow.

For the hackathon MVP, the AIS dataset is a synthetic/sample dataset rather than a complete live global AIS feed.

---

## Source Corridor & Hindcast

The attribution system uses a reverse-hindcast result containing a trajectory and source corridor.

The expected hindcast structure is:

```json
{
  "incident_id": "INC001",
  "trajectory": {
    "type": "Feature",
    "geometry": {
      "type": "LineString",
      "coordinates": []
    }
  },
  "source_corridor": {
    "type": "Feature",
    "geometry": {
      "type": "Polygon",
      "coordinates": []
    }
  }
}
```

The `source_corridor` is used as the primary spatial reference for vessel correlation.

### Geographic Convention

All API-facing GeoJSON uses:

```text
CRS: EPSG:4326 / WGS84
Coordinate order: [longitude, latitude]
```

---

## Vessel Ranking

Each AIS observation is evaluated using three main factors.

### 1. Spatial Score

Measures how close the vessel observation is to the inferred source corridor.

Closer observations receive higher scores.

### 2. Temporal Score

Measures how close the AIS observation time is to the spill detection time.

Observations closer in time receive higher scores.

### 3. Track/Corridor Score

Checks whether the vessel observation lies within the inferred source corridor.

Observations inside the corridor receive the highest track consistency score.

---

## Relevance Score

The final relevance score is calculated using:

```text
Relevance Score =
    40% × Spatial Score
  + 35% × Temporal Score
  + 25% × Track/Corridor Score
```

The resulting score is normalized to a `0–100` scale.

The system then selects the highest-ranked observations and returns the top candidate vessels.

Each vessel is represented with:

* Vessel ID
* Relevance score
* Distance from source corridor
* Time gap from detection
* Explanation

---

## Interpretation of the Score

The score represents the degree of **spatial and temporal correlation** between a vessel observation and the inferred source corridor.

A high score means that the vessel's observed position and time are strongly compatible with the modelled spill-source region.

It does **not** mean that the vessel has been proven responsible for the spill.

The system therefore uses terminology such as:

* Candidate vessel
* Relevance score
* Source corridor
* Probable source region
* Spatial/temporal correlation

rather than claiming definitive responsibility.

---

# API

## `POST /attribute`

The `/attribute` endpoint ranks candidate vessels for an oil-spill incident.

### Endpoint

```text
POST /attribute
```

### Input

The endpoint accepts:

```json
{
  "incident_id": "INC001",
  "detection_time": "2026-09-01T20:45:15.466871Z",
  "centroid": [54.48877510459397, 25.322134857980192],
  "spill_geojson": {}
}
```

### Request Fields

| Field            | Type   | Description                                                    |
| ---------------- | ------ | -------------------------------------------------------------- |
| `incident_id`    | string | Unique incident identifier                                     |
| `detection_time` | string | UTC time when the spill was detected                           |
| `centroid`       | array  | Spill centroid as `[longitude, latitude]`                      |
| `spill_geojson`  | object | Spill geometry supplied by the upstream spill-detection system |

---

## API Processing

When `/attribute` receives a request, it performs the following:

```text
POST /attribute
       │
       ▼
Validate incident information
       │
       ▼
Request / obtain hindcast
       │
       ▼
Extract source corridor
       │
       ▼
Load AIS dataset
       │
       ▼
Validate AIS fields
       │
       ▼
Apply temporal window
       │
       ▼
Calculate corridor distance
       │
       ▼
Calculate spatial score
       │
       ▼
Calculate temporal score
       │
       ▼
Check corridor intersection
       │
       ▼
Calculate relevance score
       │
       ▼
Return ranked candidates
```

---

# API Response

A successful request returns:

```json
{
  "incident_id": "INC001",
  "candidate_vessels": [
    {
      "vessel_id": "VESSEL_C",
      "relevance_score": 100,
      "distance_km": 0.0,
      "time_gap_minutes": 1,
      "reason": "Vessel position intersects the source corridor with compatible timing"
    }
  ]
}
```

### Response Fields

| Field               | Description                                          |
| ------------------- | ---------------------------------------------------- |
| `incident_id`       | Incident identifier supplied in the request          |
| `candidate_vessels` | Ranked list of candidate vessels                     |
| `vessel_id`         | AIS vessel identifier                                |
| `relevance_score`   | Overall spatial/temporal relevance score from 0–100  |
| `distance_km`       | Vessel observation distance from the source corridor |
| `time_gap_minutes`  | Time difference from spill detection                 |
| `reason`            | Human-readable explanation for the ranking           |

---

## Example Result

For a test incident, the API successfully produced a candidate such as:

```text
Incident: INC001

Candidate:
    Vessel ID: VESSEL_C
    Relevance Score: 100
    Distance: 0.0 km
    Time Gap: 1 minute
```

This indicates a strong spatial and temporal correlation with the source corridor for that observation.

It should still be interpreted as a **candidate correlation**, not confirmed responsibility.

---

# Running Locally

## 1. Clone the Repository

```bash
git clone <repository-url>
cd SIH-Team2
```

## 2. Create a Virtual Environment

```bash
python -m venv .venv
```

## 3. Activate the Environment

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

## 5. Start the API

```powershell
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

The API will then be available at:

```text
http://localhost:8000
```

---

# API Documentation

FastAPI automatically provides interactive API documentation.

After starting the server, open:

```text
http://localhost:8000/docs
```

The Swagger interface can be used to test the `/attribute` endpoint.

---

# Testing

Run the attribution test suite with:

```powershell
python -m pytest .\tests\test_attribution.py -q
```

The tests cover the attribution and scoring workflow.

---

# Design Principles

## Explainability

The ranking is based on explicit spatial and temporal factors, making the result easier to understand and validate.

## Geospatial Consistency

Geospatial calculations use appropriate projected coordinates for distance measurement while maintaining WGS84/EPSG:4326 for API-facing GeoJSON.

## Fault Tolerance

The attribution service supports a local hindcast fallback when the external hindcast service is unavailable.

## Contract Compatibility

The API follows the defined Team 2 request and response structures so that it can be integrated with the rest of the SIH system.

## Candidate-Based Attribution

The system prioritizes vessels for further investigation rather than making an unsupported definitive accusation.

---

# Limitations

This implementation is an SIH 2026 MVP and has several limitations:

* The AIS data used for demonstration is synthetic/sample data.
* The system does not currently consume a complete live AIS feed.
* Hindcast accuracy depends on the available environmental forcing and model configuration.
* The relevance score is a transparent heuristic rather than a trained causal model.
* A high relevance score does not establish that a vessel caused the spill.
* Real-world attribution would require additional evidence and independent verification.

---

# Future Improvements

Potential improvements include:

* Integration with live AIS data sources.
* Larger historical AIS datasets.
* More detailed vessel trajectory reconstruction.
* Heading and movement-direction consistency analysis.
* Improved ocean-current and wind forcing.
* Uncertainty estimation for the source corridor.
* Vessel metadata enrichment.
* Historical vessel-track analysis.
* Probabilistic attribution models.
* Integration with additional satellite observations.
* Automated evidence generation for investigation reports.

---

# Team 2 Responsibilities

Team 2 focuses on **Spill Forensics & Vessel Attribution**.

Core responsibilities include:

* Reverse oil-spill hindcasting
* Source corridor estimation
* AIS data processing
* Spatial vessel correlation
* Temporal vessel correlation
* Candidate vessel ranking
* Explainable relevance scoring
* `/hindcast` API
* `/attribute` API
* Attribution testing
* Hindcast fallback handling

---

# Project Context

This work is part of the **Smart India Hackathon 2026** project addressing oil-spill investigation using satellite imagery, ocean modelling, and vessel tracking data.

The overall objective is to combine multiple evidence sources into an investigation workflow that helps identify probable spill origins and prioritize vessels for further analysis.

```text
Satellite Observation
        +
Ocean Drift Modelling
        +
AIS Vessel Tracking
        +
Geospatial Correlation
        =
Oil Spill Investigation Support
```

---

## Disclaimer

This software is a hackathon prototype intended for research, demonstration, and decision-support purposes.

The vessel ranking represents correlation with a modelled source corridor and should not be interpreted as definitive evidence of legal or operational responsibility.
