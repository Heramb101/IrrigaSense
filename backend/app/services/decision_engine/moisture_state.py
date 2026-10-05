"""
IrrigaSense Decision Engine — Moisture State & Depletion Evaluation
===================================================================
Evaluates the continuous soil moisture state against FAO-56 Managed Allowable
Depletion (MAD) and hydrological soil constants (Field Capacity & Wilting Point).
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class MoistureStateEvaluation:
    current_moisture_vwc: float
    predicted_moisture_vwc: float
    field_capacity_vwc: float
    permanent_wilting_point_vwc: float
    mad_fraction: float
    taw_vwc: float                     # Total Available Water (FC - PWP)
    raw_vwc: float                     # Readily Available Water (MAD * TAW)
    mad_threshold_vwc: float           # Irrigation trigger line: FC - RAW
    stress_threshold_vwc: float        # Severe deficit / wilting danger line
    depletion_fraction: float          # Depleted fraction of TAW (0.0 to 1.0+)
    moisture_state: str                # SATURATED, HIGH, SAFE, DEFICIT, SEVERE_DEFICIT
    moisture_delta_24h_vwc: float      # predicted - current


def evaluate_moisture_state(
    current_moisture: float,
    predicted_moisture_24h: float,
    field_capacity: float,
    permanent_wilting_point: float,
    mad_fraction: float,
) -> MoistureStateEvaluation:
    """
    Computes hydrological soil-water balance parameters and classifies
    the predicted 24-hour moisture state.

    Standard FAO-56 Formulations:
      TAW = FC - PWP
      RAW = MAD * TAW
      Threshold_MAD = FC - RAW
      Depletion Fraction = (FC - predicted_moisture) / TAW
    """
    # Guard against invalid soil constants
    fc = max(5.0, float(field_capacity))
    pwp = max(1.0, min(float(permanent_wilting_point), fc - 2.0))
    mad = max(0.10, min(0.90, float(mad_fraction)))

    taw = fc - pwp
    raw = mad * taw
    mad_threshold = fc - raw

    # Severe stress threshold (halfway between MAD threshold and PWP, or PWP + 0.25*RAW)
    stress_threshold = max(pwp, mad_threshold - 0.5 * (mad_threshold - pwp))

    # Moisture change forecast
    delta_24h = predicted_moisture_24h - current_moisture

    # Depletion calculation
    if predicted_moisture_24h >= fc:
        depletion_frac = 0.0
    else:
        depletion_frac = (fc - predicted_moisture_24h) / taw

    # Classification logic
    if predicted_moisture_24h > fc * 1.10:
        state = "SATURATED"
    elif predicted_moisture_24h >= fc:
        state = "HIGH"
    elif predicted_moisture_24h >= mad_threshold:
        state = "SAFE"
    elif predicted_moisture_24h >= stress_threshold:
        state = "DEFICIT"
    else:
        state = "SEVERE_DEFICIT"

    return MoistureStateEvaluation(
        current_moisture_vwc=round(float(current_moisture), 2),
        predicted_moisture_vwc=round(float(predicted_moisture_24h), 2),
        field_capacity_vwc=round(fc, 2),
        permanent_wilting_point_vwc=round(pwp, 2),
        mad_fraction=round(mad, 2),
        taw_vwc=round(taw, 2),
        raw_vwc=round(raw, 2),
        mad_threshold_vwc=round(mad_threshold, 2),
        stress_threshold_vwc=round(stress_threshold, 2),
        depletion_fraction=round(float(depletion_frac), 4),
        moisture_state=state,
        moisture_delta_24h_vwc=round(float(delta_24h), 2),
    )
