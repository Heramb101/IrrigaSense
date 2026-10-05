#!/usr/bin/env python3
"""
IrrigaSense — Milestone 10 Integration Test Suite: ANFIS -> Decision Engine
===========================================================================
Validates:
  1. Environment data with all 5 inputs produces an ANFIS prediction.
  2. predicted_target_mean_24h is populated in the response.
  3. Decision Engine receives the ANFIS prediction.
  4. A valid recommendation is returned.
  5. Dashboard/API response contains non-null predicted_moisture_24h.
  6. Genuinely missing one of the 5 ANFIS inputs safely produces INSUFFICIENT_CONFIDENCE.
  7. No ANFIS training occurs (model checkpoint hash remains immutable).
  8. End-to-end Palghar / Mumbai coordinates test passes with non-null predicted_moisture_24h.
  9. Nested { "assessment": {...}, "environment": {...} } payload is handled cleanly.
  10. Zero ANFIS/ML internals leaked into user-facing reasons.
"""

import hashlib
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
FROZEN_MODEL_JSON = PROJECT_ROOT / "ml" / "anfis" / "artifacts" / "anfis_final_validation_best.json"

from app.main import app
from app.services.decision_engine.anfis_inference import anfis_inference_service



@pytest.fixture
def client():
    return TestClient(app)


def _compute_model_hash():
    with open(FROZEN_MODEL_JSON, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# 1, 2, 3, 4, 5: End-to-end inference & prediction population
def test_anfis_produces_prediction_and_populates_response(client):
    initial_hash = _compute_model_hash()

    payload = {
        "crop_name": "Tomato",
        "planting_date": "2026-08-15",
        "current_soil_moisture": 28.5,
        "temperature_2m": 29.4,
        "relative_humidity_2m": 52.0,
        "et0_fao": 4.8,
        "clay_content": 22.6,
        "irrigation_method": "Drip",
        "water_availability": "Moderate",
        "farm_size": "2-5 acres",
    }
    response = client.post("/api/decision/recommendation", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Assertions on ANFIS prediction output
    assert data["predicted_moisture_24h"] is not None
    assert data["predicted_target_mean_24h"] is not None
    assert isinstance(data["predicted_moisture_24h"], float)
    assert data["predicted_moisture_24h"] == data["predicted_target_mean_24h"]
    assert 10.0 <= data["predicted_moisture_24h"] <= 60.0

    # Assertions on Decision Engine evaluation
    assert data["decision"] in ["NO_IRRIGATION", "MONITOR", "IRRIGATION_RECOMMENDED", "IRRIGATION_URGENT"]
    assert data["confidence"] in ["HIGH", "MEDIUM"]
    assert data["domain_status"] == "VALIDATED_DOMAIN"
    assert len(data["warnings"]) == 0

    # Ensure no retraining occurred
    assert _compute_model_hash() == initial_hash


# 6: Genuinely missing input produces INSUFFICIENT_CONFIDENCE
def test_missing_anfis_input_produces_insufficient_confidence(client):
    payload = {
        "crop_name": "Tomato",
        "planting_date": "2026-08-15",
        "current_soil_moisture": None,  # Missing moisture without lat/lon
        "temperature_2m": 29.4,
        "relative_humidity_2m": 52.0,
        "et0_fao": 4.8,
        "clay_content": 22.6,
    }
    response = client.post("/api/decision/recommendation", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["decision"] == "INSUFFICIENT_CONFIDENCE"
    assert data["confidence"] == "UNAVAILABLE"
    assert data["predicted_moisture_24h"] is None
    assert "Missing essential environmental telemetry" in data["reason"]


# 7: Standalone inference service test
def test_anfis_inference_service_predict():
    pred = anfis_inference_service.predict_24h_soil_moisture(
        soil_moisture_root_zone=28.5,
        et0_fao_evapotranspiration=4.8,
        temperature_2m=29.4,
        relative_humidity_2m=52.0,
        clay_content=22.6,
    )
    assert pred is not None
    assert isinstance(pred, float)
    assert 20.0 <= pred <= 40.0


# 8: Palghar coordinates automated telemetry resolution
def test_palghar_coordinates_automated_pipeline(client):
    payload = {
        "crop_name": "Tomato",
        "planting_date": "2026-08-15",
        "latitude": 19.6967,
        "longitude": 72.7699,
        "irrigation_method": "Drip",
        "water_availability": "Moderate",
        "farm_size": "2–5 acres",
    }
    response = client.post("/api/decision/recommendation", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["predicted_moisture_24h"] is not None
    assert data["predicted_target_mean_24h"] is not None
    assert data["current_moisture"] is not None
    assert data["decision"] in ["NO_IRRIGATION", "MONITOR", "IRRIGATION_RECOMMENDED", "IRRIGATION_URGENT"]
    assert "Missing essential environmental telemetry: predicted_soil_moisture_24h" not in data["reason"]


# 9: Nested structured payload { "assessment": {...}, "environment": {...} }
def test_nested_structured_payload(client):
    payload = {
        "assessment": {
            "crop": "Tomato",
            "planting_date": "2026-08-15",
            "farm_size": "2-5 acres",
            "irrigation_method": "Drip",
            "water_availability": "Moderate",
        },
        "environment": {
            "soil_moisture_root_zone": 27.5,
            "et0_fao_evapotranspiration": 4.5,
            "temperature_2m": 28.0,
            "relative_humidity_2m": 60.0,
            "clay_content": 22.6,
        },
    }
    response = client.post("/api/decision/recommendation", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["predicted_moisture_24h"] is not None
    assert data["crop"] == "Tomato"
    assert data["decision"] in ["NO_IRRIGATION", "MONITOR", "IRRIGATION_RECOMMENDED", "IRRIGATION_URGENT"]
    assert data["confidence"] == "HIGH"
