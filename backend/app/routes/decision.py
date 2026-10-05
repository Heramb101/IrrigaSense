"""
IrrigaSense Decision Engine — API Route
=======================================
Exposes the adaptive irrigation decision engine endpoint:
POST /api/decision/recommendation
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status

from app.schemas.decision import RecommendationRequest, RecommendationResponse
from app.services.decision_engine import adaptive_decision_engine
from app.services.decision_engine.anfis_inference import anfis_inference_service
from app.services.environment.open_meteo import open_meteo_service
from app.services.environment.soilgrids import soilgrids_service

logger = logging.getLogger("irrigasense.decision_route")

router = APIRouter(
    prefix="/api/decision",
    tags=["Decision Engine"]
)


def _fetch_open_meteo_root_zone_moisture(lat: float, lon: float) -> Optional[float]:
    """Queries Open-Meteo for root-zone volumetric soil moisture (% VWC)."""
    try:
        import httpx
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "soil_moisture_7_to_28cm,soil_moisture_0_to_7cm",
            "timezone": "auto",
        }
        with httpx.Client(timeout=6.0) as client:
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json().get("current", {})
                m = data.get("soil_moisture_7_to_28cm")
                if m is None:
                    m = data.get("soil_moisture_0_to_7cm")
                if m is not None:
                    return round(float(m) * 100.0, 1)
    except Exception as e:
        logger.warning("Failed to fetch root-zone soil moisture from Open-Meteo: %s", str(e))
    return None


@router.post(
    "/recommendation",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get adaptive irrigation recommendation",
    description=(
        "Converts observed root-zone soil moisture, ANFIS 24-hour forecast, and farmer operational context "
        "into a deterministic crop-specific irrigation decision (NO_IRRIGATION, MONITOR, IRRIGATION_RECOMMENDED, "
        "IRRIGATION_URGENT, INSUFFICIENT_CONFIDENCE)."
    )
)
def get_irrigation_recommendation(request: RecommendationRequest) -> RecommendationResponse:
    """Evaluates farm inputs against the adaptive decision engine."""
    # 1. Harmonize assessment fields (supports both flat and nested 'assessment' object)
    crop_name = request.crop_name
    planting_date = request.planting_date
    irrigation_method = request.irrigation_method or "Drip"
    water_availability = request.water_availability or "Medium"
    farm_size = request.farm_size or "1-2 acres"
    lat = request.latitude
    lon = request.longitude

    if request.assessment:
        asmt = request.assessment if isinstance(request.assessment, dict) else request.assessment.model_dump()
        crop_name = asmt.get("crop") or asmt.get("crop_name") or crop_name
        planting_date = asmt.get("planting_date") or planting_date
        irrigation_method = asmt.get("irrigation_method") or irrigation_method
        water_availability = asmt.get("water_availability") or water_availability
        farm_size = asmt.get("farm_size") or farm_size
        if lat is None:
            lat = asmt.get("latitude")
        if lon is None:
            lon = asmt.get("longitude")

    if not crop_name:
        crop_name = "Tomato"
    if not planting_date:
        planting_date = "2026-08-15"

    # 2. Harmonize environmental telemetry fields (supports flat and nested 'environment')
    current_moisture = request.current_soil_moisture
    predicted_moisture = request.predicted_moisture_24h
    if predicted_moisture is None and request.predicted_target_mean_24h is not None:
        predicted_moisture = request.predicted_target_mean_24h

    temp = request.temperature_2m
    rh = request.relative_humidity_2m
    et0 = request.et0_fao
    clay = request.clay_content
    precip = 0.0

    if request.environment:
        env = request.environment if isinstance(request.environment, dict) else request.environment.model_dump()
        if current_moisture is None:
            current_moisture = env.get("soil_moisture_root_zone") or env.get("soil_moisture")
        if et0 is None:
            et0 = env.get("et0_fao_evapotranspiration") or env.get("et0")
        if temp is None:
            temp = env.get("temperature_2m") or env.get("temperature")
        if rh is None:
            rh = env.get("relative_humidity_2m") or env.get("humidity")
        if clay is None:
            clay = env.get("clay_content") or env.get("clay")
        if "precipitation" in env:
            precip = float(env["precipitation"] or 0.0)

    # 3. Auto-resolve telemetry from coordinates if coordinates are available
    if lat is not None and lon is not None:
        # Weather resolution
        if temp is None or rh is None or et0 is None:
            try:
                env_resp = open_meteo_service.get_weather_profile(lat, lon)
                if temp is None:
                    temp = env_resp.weather.temperature_c
                if rh is None:
                    rh = env_resp.weather.humidity_percent
                if et0 is None:
                    et0 = env_resp.weather.et0_mm
                precip = env_resp.weather.precipitation_mm
            except Exception as e:
                logger.warning("Could not fetch Open-Meteo weather profile: %s", str(e))

        # Soil moisture resolution (Open-Meteo 7-28cm active root zone)
        if current_moisture is None:
            current_moisture = _fetch_open_meteo_root_zone_moisture(lat, lon)

        # Clay resolution (ISRIC SoilGrids topsoil)
        if clay is None:
            try:
                soil_resp = soilgrids_service.get_soil_profile(lat, lon)
                if soil_resp.soil.clay_percent is not None:
                    clay = soil_resp.soil.clay_percent
                else:
                    # Regional baseline mineral soil clay content when SoilGrids lacks coverage
                    clay = 22.6
            except Exception as e:
                logger.warning("Could not fetch SoilGrids clay percentage: %s", str(e))
                clay = 22.6

    # Baseline mineral soil fallback for clay if missing from survey
    if clay is None:
        clay = 22.6

    # 4. Generate ANFIS Prediction if not explicitly provided
    if predicted_moisture is None:
        logger.info(
            "Generating ANFIS 24h soil moisture forecast for crop=%s (lat=%s, lon=%s)",
            crop_name,
            lat,
            lon,
        )
        predicted_moisture = anfis_inference_service.predict_24h_soil_moisture(
            soil_moisture_root_zone=current_moisture,
            et0_fao_evapotranspiration=et0,
            temperature_2m=temp,
            relative_humidity_2m=rh,
            clay_content=clay,
        )

    # 5. Execute Milestone 9 Decision Engine
    result = adaptive_decision_engine.evaluate_recommendation(
        current_moisture=current_moisture,
        predicted_moisture_24h=predicted_moisture,
        crop_name=crop_name,
        planting_date=planting_date,
        clay_content=clay,
        temperature_2m=temp,
        relative_humidity_2m=rh,
        et0_fao=et0,
        irrigation_method=irrigation_method,
        water_availability=water_availability,
        farm_size=farm_size,
        current_date=request.evaluation_date,
    )



    # Populate response fields
    result["predicted_target_mean_24h"] = predicted_moisture
    result["weather_summary"] = {
        "temperature_c": temp,
        "humidity_percent": rh,
        "et0_mm": et0,
        "precipitation_mm": precip,
    }
    result["last_updated"] = datetime.now().isoformat()

    return RecommendationResponse(**result)
