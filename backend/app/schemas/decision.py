"""
IrrigaSense Decision Engine — API Schemas
=========================================
Pydantic schemas for the decision engine recommendation endpoint.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class DecisionContext(BaseModel):
    """Contextual metadata surrounding the irrigation decision."""
    irrigation_method: str = Field(default="Drip", description="Application method (Drip, Sprinkler, Flood, Other)")
    water_availability: str = Field(default="Medium", description="Farmer water security constraint (High, Medium, Low)")
    farm_size: str = Field(default="1-2 acres", description="Farm scale contextual classification")


class RecommendationRequest(BaseModel):
    """
    Request payload for an adaptive irrigation decision recommendation.
    Supports flat fields, nested assessment/environment structures, or coordinate-based automated lookup.
    """
    # Flat / legacy fields
    crop_name: Optional[str] = Field(None, description="Crop name (e.g. 'Tomato', 'Zucchini', 'Blueberry')", examples=["Tomato"])
    planting_date: Optional[Union[date, str]] = Field(None, description="Crop sowing/transplant date (YYYY-MM-DD)", examples=["2025-06-15"])
    current_soil_moisture: Optional[float] = Field(None, description="Current in-situ or Open-Meteo root-zone moisture (% VWC)", examples=[28.5])
    predicted_moisture_24h: Optional[float] = Field(
        None,
        description="Predicted 24h soil moisture from ANFIS (% VWC). If omitted, will be inferred from environmental telemetry."
    )
    predicted_target_mean_24h: Optional[float] = Field(
        None,
        description="Direct ANFIS prediction output alias (% VWC)"
    )
    # Environmental telemetry for domain check / ANFIS fallback
    clay_content: Optional[float] = Field(None, description="Soil clay content from SoilGrids or survey (%)", examples=[22.6])
    temperature_2m: Optional[float] = Field(None, description="Ambient air temperature (°C)", examples=[24.5])
    relative_humidity_2m: Optional[float] = Field(None, description="Ambient relative humidity (%)", examples=[55.0])
    et0_fao: Optional[float] = Field(None, description="FAO-56 reference evapotranspiration (mm/day)", examples=[4.5])
    # Farmer context
    irrigation_method: Optional[str] = Field(default="Drip", description="Irrigation method (Drip, Sprinkler, Flood, Other)")
    water_availability: Optional[str] = Field(default="Medium", description="Water availability (High, Medium, Low)")
    farm_size: Optional[str] = Field(default="1-2 acres", description="Farm size classification")
    evaluation_date: Optional[Union[date, str]] = Field(default=None, description="Optional custom evaluation date")
    # Location coordinates for automated environmental telemetry lookup
    latitude: Optional[float] = Field(default=None, description="Farm latitude in decimal degrees")
    longitude: Optional[float] = Field(default=None, description="Farm longitude in decimal degrees")
    # Nested structured payloads
    assessment: Optional[Dict[str, Any]] = Field(None, description="Farmer assessment object (crop, planting_date, farm_size, etc.)")
    environment: Optional[Dict[str, Any]] = Field(None, description="Telemetry object (soil_moisture_root_zone, et0, temp, rh, clay)")


class RecommendationResponse(BaseModel):
    """Standardized agronomic irrigation recommendation response."""
    decision: str = Field(
        ...,
        description="Core decision state: NO_IRRIGATION, MONITOR, IRRIGATION_RECOMMENDED, IRRIGATION_URGENT, INSUFFICIENT_CONFIDENCE"
    )
    confidence: str = Field(
        ...,
        description="Decision reliability classification: HIGH, MEDIUM, LOW, UNAVAILABLE"
    )
    current_moisture: Optional[float] = Field(None, description="Observed current root-zone moisture (% VWC)")
    predicted_moisture_24h: Optional[float] = Field(None, description="Forecasted 24-hour root-zone moisture (% VWC)")
    predicted_target_mean_24h: Optional[float] = Field(None, description="Direct ANFIS prediction value (% VWC)")
    field_capacity: Optional[float] = Field(None, description="Soil/substrate Field Capacity (% VWC)")
    mad_threshold: Optional[float] = Field(None, description="Crop-specific Managed Allowable Depletion line (% VWC)")
    depletion_fraction: Optional[float] = Field(None, description="Fraction of Total Available Water currently depleted (0.0 - 1.0+)")
    moisture_state: Optional[str] = Field(None, description="Hydrological regime: SATURATED, HIGH, SAFE, DEFICIT, SEVERE_DEFICIT, UNKNOWN")
    crop: str = Field(..., description="Canonical crop name")
    crop_stage: str = Field(..., description="Resolved growth stage from Days After Planting (DAP)")

    dap: Optional[int] = Field(None, description="Days After Planting elapsed")
    reason: str = Field(..., description="Clear farmer-facing explanation of the recommendation")
    domain_status: str = Field(..., description="Domain check status: VALIDATED_DOMAIN or GUARDRAIL_TRIGGERED")
    warnings: List[str] = Field(default_factory=list, description="Specific warnings or guardrail alerts")
    context: DecisionContext = Field(default_factory=DecisionContext, description="Farmer operational context")
    weather_summary: Optional[Dict[str, Any]] = Field(default=None, description="Environmental weather summary for dashboard display")
    last_updated: Optional[str] = Field(default=None, description="ISO-8601 timestamp when recommendation was generated")

    model_config = ConfigDict(from_attributes=True)

