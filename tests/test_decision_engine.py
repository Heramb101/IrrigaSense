#!/usr/bin/env python3
"""
IrrigaSense — Milestone 9 Test Suite: Adaptive Irrigation Decision Engine
=========================================================================
Validates:
  1. Safe moisture -> NO_IRRIGATION.
  2. Approaching MAD depletion boundary -> MONITOR.
  3. Below MAD threshold -> IRRIGATION_RECOMMENDED.
  4. Severe deficit / near wilting point -> IRRIGATION_URGENT.
  5. Missing or unregistered crop profile -> INSUFFICIENT_CONFIDENCE.
  6. Missing or unvalidated MAD/FC -> INSUFFICIENT_CONFIDENCE.
  7. Out-of-domain moisture (<0 or >100) -> INSUFFICIENT_CONFIDENCE.
  8. Out-of-domain clay / Milestone 8D desiccated substrate -> Guardrail triggered.
  9. Limited water availability does not suppress genuine irrigation warnings.
  10. Planting date correctly computes Days After Planting (DAP).
  11. Crop stage transitions accurately according to configured DAP boundaries.
  12. Irrigation method is preserved in operational recommendation context.
  13. Farm size is preserved as context without generating unsupported volume estimates.
  14. Zero ANFIS parameters or checkpoint weights are altered during decision evaluation.
  15. Recommendation output is completely deterministic across repeated evaluations.
  16. FastAPI endpoint POST /api/decision/recommendation operates cleanly.
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.decision_engine import (
    crop_profile_manager,
    evaluate_moisture_state,
    check_domain_guardrails,
    adaptive_decision_engine,
)
from ml.anfis.anfis_model import ANFISModel

FROZEN_MODEL_JSON = PROJECT_ROOT / "ml" / "anfis" / "artifacts" / "anfis_final_validation_best.json"


@pytest.fixture
def client():
    return TestClient(app)


# 1. Safe moisture -> NO_IRRIGATION
def test_safe_moisture_yields_no_irrigation():
    # Tomato in mineral soil: FC = 32.0, MAD = 0.40, PWP = 14.0 -> TAW=18, RAW=7.2, MAD_thresh=24.8%
    # If predicted moisture is 30.0% (> 24.8 + buffer), should be NO_IRRIGATION
    res = adaptive_decision_engine.evaluate_recommendation(
        current_moisture=31.0,
        predicted_moisture_24h=30.0,
        crop_name="Tomato",
        planting_date=date.today() - timedelta(days=40),
        clay_content=22.6,
        temperature_2m=24.0,
        relative_humidity_2m=55.0,
        et0_fao=4.2,
    )
    assert res["decision"] == "NO_IRRIGATION"
    assert res["moisture_state"] in ["SAFE", "HIGH"]
    assert res["confidence"] == "HIGH"
    assert "comfortably above" in res["reason"] or "No irrigation is recommended" in res["reason"]


# 2. Approaching MAD -> MONITOR
def test_approaching_mad_yields_monitor():
    # Tomato MAD threshold is 24.8%. If predicted is 25.5% on a drying trend (current=28.0%), should MONITOR
    res = adaptive_decision_engine.evaluate_recommendation(
        current_moisture=28.0,
        predicted_moisture_24h=25.5,
        crop_name="Tomato",
        planting_date=date.today() - timedelta(days=40),
        clay_content=22.6,
        temperature_2m=26.0,
        relative_humidity_2m=50.0,
        et0_fao=5.0,
    )
    assert res["decision"] == "MONITOR"
    assert res["moisture_state"] == "SAFE"
    assert "approaching the allowable depletion" in res["reason"]


# 3. Below MAD -> IRRIGATION_RECOMMENDED
def test_below_mad_yields_irrigation_recommended():
    # Tomato MAD threshold is 24.8%. If predicted is 23.0%, should be IRRIGATION_RECOMMENDED
    res = adaptive_decision_engine.evaluate_recommendation(
        current_moisture=26.0,
        predicted_moisture_24h=23.0,
        crop_name="Tomato",
        planting_date=date.today() - timedelta(days=50),
        clay_content=22.6,
        temperature_2m=28.0,
        relative_humidity_2m=45.0,
        et0_fao=5.5,
    )
    assert res["decision"] == "IRRIGATION_RECOMMENDED"
    assert res["moisture_state"] == "DEFICIT"
    assert res["depletion_fraction"] > 0.40
    assert "fall below the crop-specific allowable depletion" in res["reason"]


# 4. Severe deficit -> IRRIGATION_URGENT
def test_severe_deficit_yields_irrigation_urgent():
    # If predicted moisture drops to 16.0% (near PWP=14.0%), should be IRRIGATION_URGENT
    res = adaptive_decision_engine.evaluate_recommendation(
        current_moisture=18.0,
        predicted_moisture_24h=16.0,
        crop_name="Tomato",
        planting_date=date.today() - timedelta(days=60),
        clay_content=22.6,
        temperature_2m=32.0,
        relative_humidity_2m=35.0,
        et0_fao=6.5,
    )
    assert res["decision"] == "IRRIGATION_URGENT"
    assert res["moisture_state"] == "SEVERE_DEFICIT"
    assert "Urgent irrigation required" in res["reason"]


# 5. Missing crop profile -> INSUFFICIENT_CONFIDENCE
def test_missing_crop_profile_yields_insufficient_confidence():
    res = adaptive_decision_engine.evaluate_recommendation(
        current_moisture=25.0,
        predicted_moisture_24h=22.0,
        crop_name="DragonFruitUnregisteredCropXYZ",
        planting_date=date.today() - timedelta(days=30),
        clay_content=22.6,
        temperature_2m=25.0,
        relative_humidity_2m=50.0,
        et0_fao=4.0,
    )
    assert res["decision"] == "INSUFFICIENT_CONFIDENCE"
    assert res["confidence"] == "UNAVAILABLE"
    assert res["domain_status"] == "GUARDRAIL_TRIGGERED"
    assert "DragonFruitUnregisteredCropXYZ" in res["reason"]


# 6. Missing MAD / unvalidated parameters -> INSUFFICIENT_CONFIDENCE
def test_unvalidated_mad_yields_insufficient_confidence():
    # Pass a simulated unvalidated crop mock
    guard = check_domain_guardrails(
        current_moisture=25.0,
        predicted_moisture_24h=22.0,
        clay_content=22.6,
        temperature_2m=25.0,
        relative_humidity_2m=50.0,
        et0_fao=4.0,
        crop_profile={"crop_id": "test_crop"},
        field_capacity=None,  # Missing FC
        mad_fraction=None,    # Missing MAD
        crop_name="TestCrop",
    )
    assert guard.is_safe is False
    assert guard.domain_status == "GUARDRAIL_TRIGGERED"
    assert guard.confidence == "UNAVAILABLE"
    assert "require agronomic validation" in guard.primary_reason


# 7. Out-of-domain moisture (<0 or >100) -> INSUFFICIENT_CONFIDENCE
def test_out_of_domain_moisture_triggers_guardrail():
    # Negative predicted moisture
    res_neg = adaptive_decision_engine.evaluate_recommendation(
        current_moisture=20.0,
        predicted_moisture_24h=-5.2,
        crop_name="Tomato",
        planting_date=date.today() - timedelta(days=30),
        clay_content=22.6,
        temperature_2m=25.0,
        relative_humidity_2m=50.0,
        et0_fao=4.0,
    )
    assert res_neg["decision"] == "INSUFFICIENT_CONFIDENCE"
    assert res_neg["domain_status"] == "GUARDRAIL_TRIGGERED"
    assert "outside physical volumetric bounds" in res_neg["reason"]

    # Moisture > 100%
    res_high = adaptive_decision_engine.evaluate_recommendation(
        current_moisture=20.0,
        predicted_moisture_24h=105.0,
        crop_name="Tomato",
        planting_date=date.today() - timedelta(days=30),
        clay_content=22.6,
        temperature_2m=25.0,
        relative_humidity_2m=50.0,
        et0_fao=4.0,
    )
    assert res_high["decision"] == "INSUFFICIENT_CONFIDENCE"
    assert res_high["domain_status"] == "GUARDRAIL_TRIGGERED"


# 8. Out-of-domain clay / Milestone 8D desiccated substrate -> Guardrail triggered
def test_milestone_8d_soilless_drydown_guardrail():
    # Clay <= 2.0 (soilless substrate) AND moisture < 15% VWC
    res = adaptive_decision_engine.evaluate_recommendation(
        current_moisture=8.0,
        predicted_moisture_24h=6.0,
        crop_name="Blueberry",
        planting_date=date.today() - timedelta(days=90),
        clay_content=0.0,  # Potted substrate
        temperature_2m=25.0,
        relative_humidity_2m=50.0,
        et0_fao=4.0,
    )
    assert res["decision"] == "INSUFFICIENT_CONFIDENCE"
    assert res["confidence"] == "UNAVAILABLE"
    assert res["domain_status"] == "GUARDRAIL_TRIGGERED"
    assert "extreme soilless substrate desiccation" in res["reason"]


# 9. Limited water does not hide genuine irrigation need
def test_limited_water_does_not_suppress_deficit():
    res = adaptive_decision_engine.evaluate_recommendation(
        current_moisture=24.0,
        predicted_moisture_24h=21.0,
        crop_name="Tomato",
        planting_date=date.today() - timedelta(days=50),
        clay_content=22.6,
        temperature_2m=27.0,
        relative_humidity_2m=45.0,
        et0_fao=5.0,
        water_availability="Low",  # Limited water
    )
    # Must STILL recommend irrigation!
    assert res["decision"] == "IRRIGATION_RECOMMENDED"
    # But explanation highlights water conservation scheduling
    assert "Water availability is limited" in res["reason"]


# 10. Planting date correctly determines DAP
def test_planting_date_computes_dap():
    today = date(2025, 7, 20)
    planting = date(2025, 6, 10)  # exactly 40 days
    profile = crop_profile_manager.get_crop_profile("Tomato")

    dap, stage_key, stage_name = crop_profile_manager.calculate_dap_and_stage(
        crop_profile=profile,
        planting_date=planting,
        current_date=today,
    )
    assert dap == 40
    assert stage_key == "vegetative"


# 11. Crop stage changes according to configured stage boundaries
def test_crop_stage_transitions():
    profile = crop_profile_manager.get_crop_profile("Zucchini")
    # Zucchini stages: initial 0-20, vegetative 21-50, mid_season 51-80, late_season 81-105
    ref_date = date(2025, 6, 1)

    # 10 days -> initial
    dap1, key1, _ = crop_profile_manager.calculate_dap_and_stage(profile, ref_date, date(2025, 6, 11))
    assert dap1 == 10
    assert key1 == "initial"

    # 35 days -> vegetative
    dap2, key2, _ = crop_profile_manager.calculate_dap_and_stage(profile, ref_date, date(2025, 7, 6))
    assert dap2 == 35
    assert key2 == "vegetative"

    # 65 days -> mid_season
    dap3, key3, _ = crop_profile_manager.calculate_dap_and_stage(profile, ref_date, date(2025, 8, 5))
    assert dap3 == 65
    assert key3 == "mid_season"

    # 90 days -> late_season
    dap4, key4, _ = crop_profile_manager.calculate_dap_and_stage(profile, ref_date, date(2025, 8, 30))
    assert dap4 == 90
    assert key4 == "late_season"


# 12. Irrigation method is retained in recommendation context
def test_irrigation_method_in_context():
    res = adaptive_decision_engine.evaluate_recommendation(
        current_moisture=26.0,
        predicted_moisture_24h=22.0,
        crop_name="Zucchini",
        planting_date=date.today() - timedelta(days=35),
        clay_content=22.6,
        temperature_2m=26.0,
        relative_humidity_2m=50.0,
        et0_fao=4.5,
        irrigation_method="Sprinkler",
    )
    assert res["context"]["irrigation_method"] == "Sprinkler"
    assert "sprinkler" in res["reason"].lower()


# 13. Farm size does not produce unsupported irrigation volume
def test_farm_size_does_not_produce_unsupported_volume():
    res = adaptive_decision_engine.evaluate_recommendation(
        current_moisture=26.0,
        predicted_moisture_24h=22.0,
        crop_name="Tomato",
        planting_date=date.today() - timedelta(days=45),
        clay_content=22.6,
        temperature_2m=26.0,
        relative_humidity_2m=50.0,
        et0_fao=4.5,
        farm_size="5-10 acres",
    )
    assert res["context"]["farm_size"] == "5-10 acres"
    # Verify no unvalidated volume keys (like "litres" or "duration_minutes") were fabricated
    assert "irrigation_litres" not in res
    assert "duration_minutes" not in res


# 14. No ANFIS parameters are modified
def test_no_anfis_parameters_are_modified():
    with open(FROZEN_MODEL_JSON, "r", encoding="utf-8") as f:
        before_dict = json.load(f)

    # Execute multiple recommendations
    for _ in range(5):
        adaptive_decision_engine.evaluate_recommendation(
            current_moisture=25.0,
            predicted_moisture_24h=20.0,
            crop_name="Tomato",
            planting_date=date.today() - timedelta(days=30),
            clay_content=22.6,
            temperature_2m=25.0,
            relative_humidity_2m=50.0,
            et0_fao=4.0,
        )

    with open(FROZEN_MODEL_JSON, "r", encoding="utf-8") as f:
        after_dict = json.load(f)

    assert before_dict == after_dict, "Frozen ANFIS checkpoint was mutated!"


# 15. Recommendation is deterministic
def test_recommendation_is_deterministic():
    args = {
        "current_moisture": 27.5,
        "predicted_moisture_24h": 22.8,
        "crop_name": "Tomato",
        "planting_date": "2025-06-15",
        "clay_content": 22.6,
        "temperature_2m": 26.5,
        "relative_humidity_2m": 52.0,
        "et0_fao": 4.8,
        "irrigation_method": "Drip",
        "water_availability": "Medium",
        "farm_size": "2-5 acres",
        "current_date": "2025-07-25",
    }
    run1 = adaptive_decision_engine.evaluate_recommendation(**args)
    run2 = adaptive_decision_engine.evaluate_recommendation(**args)
    assert run1 == run2, "Decision engine outputs are non-deterministic!"


# 16. FastAPI endpoint test
def test_api_recommendation_endpoint(client):
    payload = {
        "crop_name": "Tomato",
        "planting_date": "2025-06-01",
        "current_soil_moisture": 30.0,
        "predicted_moisture_24h": 22.0,
        "clay_content": 22.6,
        "temperature_2m": 28.0,
        "relative_humidity_2m": 45.0,
        "et0_fao": 5.2,
        "irrigation_method": "Drip",
        "water_availability": "High",
        "farm_size": "1-2 acres",
        "evaluation_date": "2025-07-15",
    }
    response = client.post("/api/decision/recommendation", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] in ["IRRIGATION_RECOMMENDED", "IRRIGATION_URGENT"]
    assert data["crop"] == "Tomato"
    assert data["dap"] == 44
    assert data["confidence"] == "HIGH"
    assert data["domain_status"] == "VALIDATED_DOMAIN"
