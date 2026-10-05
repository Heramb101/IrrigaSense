"""
IrrigaSense Decision Engine — Domain Guardrails (ML / Standalone Export)
========================================================================
Exports domain guardrails functions for offline verification and testing.
"""

from typing import Any, Dict, List, Optional, Tuple


class DomainGuardrailResult:
    """Encapsulates the outcome of domain safety checks."""

    def __init__(
        self,
        is_safe: bool,
        domain_status: str,
        confidence: str,
        primary_reason: Optional[str] = None,
        warnings: Optional[List[str]] = None,
    ):
        self.is_safe = is_safe
        self.domain_status = domain_status
        self.confidence = confidence
        self.primary_reason = primary_reason or ""
        self.warnings = warnings or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "domain_status": self.domain_status,
            "confidence": self.confidence,
            "primary_reason": self.primary_reason,
            "warnings": self.warnings,
        }


def check_domain_guardrails(
    current_moisture: Optional[float],
    predicted_moisture_24h: Optional[float],
    clay_content: Optional[float],
    temperature_2m: Optional[float],
    relative_humidity_2m: Optional[float],
    et0_fao: Optional[float],
    crop_profile: Optional[Dict[str, Any]],
    field_capacity: Optional[float],
    mad_fraction: Optional[float],
    crop_name: str = "",
) -> DomainGuardrailResult:
    """
    Evaluates inputs against validated operational domain boundaries.
    Returns a DomainGuardrailResult indicating whether the decision engine
    has sufficient confidence to proceed.
    """
    warnings: List[str] = []

    # 1. Missing Environmental Inputs
    missing_fields = []
    if current_moisture is None:
        missing_fields.append("soil_moisture")
    if predicted_moisture_24h is None:
        missing_fields.append("predicted_soil_moisture_24h")
    if clay_content is None:
        missing_fields.append("clay_content")
    if temperature_2m is None:
        missing_fields.append("temperature_2m")
    if relative_humidity_2m is None:
        missing_fields.append("relative_humidity_2m")
    if et0_fao is None:
        missing_fields.append("et0_fao_evapotranspiration")

    if missing_fields:
        return DomainGuardrailResult(
            is_safe=False,
            domain_status="GUARDRAIL_TRIGGERED",
            confidence="UNAVAILABLE",
            primary_reason=f"Missing essential environmental telemetry: {', '.join(missing_fields)}.",
            warnings=[f"Telemetry missing for: {', '.join(missing_fields)}"],
        )

    # 2. Missing Crop Profile
    if not crop_profile:
        return DomainGuardrailResult(
            is_safe=False,
            domain_status="GUARDRAIL_TRIGGERED",
            confidence="UNAVAILABLE",
            primary_reason=f"Crop '{crop_name or 'Unspecified'}' is not registered in the verified agronomic knowledge base.",
            warnings=[f"Unrecognized crop identifier: '{crop_name}'"],
        )

    # 3. Missing Agronomic Thresholds (FC or MAD)
    if field_capacity is None or mad_fraction is None:
        return DomainGuardrailResult(
            is_safe=False,
            domain_status="GUARDRAIL_TRIGGERED",
            confidence="UNAVAILABLE",
            primary_reason=f"Essential agronomic thresholds (Field Capacity or MAD) for crop '{crop_name}' require agronomic validation.",
            warnings=["Crop profile parameters marked as 'REQUIRES AGRONOMIC VALIDATION'."],
        )

    # 4. Out-of-Bounds Predicted Moisture (Numerical Extrapolation Check)
    if predicted_moisture_24h < 0.0 or predicted_moisture_24h > 100.0:
        return DomainGuardrailResult(
            is_safe=False,
            domain_status="GUARDRAIL_TRIGGERED",
            confidence="UNAVAILABLE",
            primary_reason=f"Predicted soil moisture ({predicted_moisture_24h:.1f}% VWC) extrapolates outside physical volumetric bounds [0, 100]% VWC.",
            warnings=[f"Model prediction outside physical bounds: {predicted_moisture_24h:.2f}% VWC"],
        )

    # 5. Out-of-Bounds Input Sensor Moisture
    if current_moisture < 0.0 or current_moisture > 100.0:
        return DomainGuardrailResult(
            is_safe=False,
            domain_status="GUARDRAIL_TRIGGERED",
            confidence="UNAVAILABLE",
            primary_reason=f"Current sensor soil moisture ({current_moisture:.1f}% VWC) violates physical limits.",
            warnings=[f"Sensor soil moisture out of bounds: {current_moisture:.2f}% VWC"],
        )

    # 6. Out-of-Bounds Clay Content
    if clay_content < 0.0 or clay_content > 60.0:
        return DomainGuardrailResult(
            is_safe=False,
            domain_status="GUARDRAIL_TRIGGERED",
            confidence="UNAVAILABLE",
            primary_reason=f"Soil clay content ({clay_content:.1f}%) is outside the validated agricultural domain [0, 60]%.",
            warnings=[f"Clay content outside validated domain: {clay_content:.1f}%"],
        )

    # 7. Milestone 8D Specific Finding: Soilless Substrate Severe Desiccation Extrapolation
    if clay_content <= 2.0 and (current_moisture < 15.0 or predicted_moisture_24h < 15.0):
        return DomainGuardrailResult(
            is_safe=False,
            domain_status="GUARDRAIL_TRIGGERED",
            confidence="UNAVAILABLE",
            primary_reason="Input combination represents an unvalidated extreme soilless substrate desiccation regime (clay ≤ 2% with moisture < 15% VWC). The neuro-fuzzy model has unverified reliability in this domain.",
            warnings=["Triggered Milestone 8D soilless substrate desiccation guardrail."],
        )

    # 8. Meteorological Physical Bounds
    if temperature_2m < -15.0 or temperature_2m > 55.0:
        warnings.append(f"Ambient temperature ({temperature_2m:.1f}°C) is near extreme limits.")
    if relative_humidity_2m < 5.0 or relative_humidity_2m > 100.0:
        warnings.append(f"Relative humidity ({relative_humidity_2m:.1f}%) is outside typical sensor range.")
    if et0_fao < 0.0 or et0_fao > 18.0:
        warnings.append(f"Reference ET₀ ({et0_fao:.2f} mm/day) is unusually extreme.")

    # 9. Severe 24h Volumetric Delta (Rate-of-Change Anomaly Check)
    if abs(predicted_moisture_24h - current_moisture) > 45.0:
        warnings.append("Predicted 24-hour moisture shift exceeds 45% VWC; rapid recharge or sensor transition indicated.")

    confidence = "HIGH"
    if len(warnings) > 1:
        confidence = "LOW"
    elif len(warnings) == 1:
        confidence = "MEDIUM"

    return DomainGuardrailResult(
        is_safe=True,
        domain_status="VALIDATED_DOMAIN",
        confidence=confidence,
        primary_reason="All inputs lie within the validated agro-meteorological operating envelope.",
        warnings=warnings,
    )
