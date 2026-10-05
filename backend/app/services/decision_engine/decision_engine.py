"""
IrrigaSense Decision Engine — Core Decision Orchestrator
========================================================
Decouples prediction from agronomic decision-making. Evaluates ANFIS 24-hour
soil moisture forecasts against crop-specific Managed Allowable Depletion (MAD),
growth stage (DAP), irrigation method context, and water availability constraints.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

from app.services.decision_engine.crop_profiles import crop_profile_manager
from app.services.decision_engine.domain_guardrails import check_domain_guardrails
from app.services.decision_engine.moisture_state import evaluate_moisture_state


class AdaptiveDecisionEngine:
    """Deterministic rule-based agronomic decision layer."""

    def evaluate_recommendation(
        self,
        current_moisture: Optional[float],
        predicted_moisture_24h: Optional[float],
        crop_name: str,
        planting_date: Union[date, str, datetime],
        clay_content: Optional[float] = 22.6,
        temperature_2m: Optional[float] = None,
        relative_humidity_2m: Optional[float] = None,
        et0_fao: Optional[float] = None,
        irrigation_method: Optional[str] = "Drip",
        water_availability: Optional[str] = "Medium",
        farm_size: Optional[str] = "1-2 acres",
        current_date: Optional[Union[date, str, datetime]] = None,
    ) -> Dict[str, Any]:
        """
        Executes the deterministic agronomic decision pipeline.
        Returns a standardized recommendation dictionary.
        """
        method_str = str(irrigation_method or "Drip").strip()
        water_avail_str = str(water_availability or "Medium").strip()
        farm_size_str = str(farm_size or "Unspecified").strip()

        # 1. Lookup Crop Profile
        crop_profile = crop_profile_manager.get_crop_profile(crop_name)
        canonical_crop_name = crop_profile.get("crop_name", crop_name) if crop_profile else crop_name

        # Detect soilless potting condition (clay <= 2.0 or potted crop)
        is_soilless = (clay_content is not None and clay_content <= 2.0) or ("pot" in str(crop_name).lower())

        # 2. Extract Soil & Crop Thresholds
        fc, pwp, mad, stress = crop_profile_manager.get_crop_thresholds(crop_profile, is_soilless=is_soilless)

        # 3. Calculate DAP and Crop Growth Stage
        dap, stage_key, stage_name = crop_profile_manager.calculate_dap_and_stage(
            crop_profile=crop_profile,
            planting_date=planting_date,
            current_date=current_date,
        )

        # 4. Enforce Domain Guardrails
        guardrail_result = check_domain_guardrails(
            current_moisture=current_moisture,
            predicted_moisture_24h=predicted_moisture_24h,
            clay_content=clay_content,
            temperature_2m=temperature_2m,
            relative_humidity_2m=relative_humidity_2m,
            et0_fao=et0_fao,
            crop_profile=crop_profile,
            field_capacity=fc,
            mad_fraction=mad,
            crop_name=canonical_crop_name,
        )

        if not guardrail_result.is_safe:
            return {
                "decision": "INSUFFICIENT_CONFIDENCE",
                "confidence": guardrail_result.confidence,
                "current_moisture": current_moisture,
                "predicted_moisture_24h": predicted_moisture_24h,
                "field_capacity": fc,
                "mad_threshold": None,
                "depletion_fraction": None,
                "moisture_state": "UNKNOWN",
                "crop": canonical_crop_name,
                "crop_stage": stage_name,
                "dap": dap,
                "reason": (
                    "The system cannot safely make an irrigation recommendation because current conditions "
                    f"fall outside the validated operating range: {guardrail_result.primary_reason}"
                ),
                "domain_status": guardrail_result.domain_status,
                "warnings": guardrail_result.warnings,
                "context": {
                    "irrigation_method": method_str,
                    "water_availability": water_avail_str,
                    "farm_size": farm_size_str,
                },
            }

        # 5. Evaluate Moisture State & Depletion
        assert current_moisture is not None
        assert predicted_moisture_24h is not None
        assert fc is not None
        assert pwp is not None
        assert mad is not None

        moisture_eval = evaluate_moisture_state(
            current_moisture=current_moisture,
            predicted_moisture_24h=predicted_moisture_24h,
            field_capacity=fc,
            permanent_wilting_point=pwp,
            mad_fraction=mad,
        )

        # 6. Determine Decision State
        mad_threshold = moisture_eval.mad_threshold_vwc
        stress_threshold = moisture_eval.stress_threshold_vwc
        raw_span = moisture_eval.raw_vwc
        monitor_buffer = 0.20 * raw_span  # Approach buffer within 20% of RAW

        warnings = list(guardrail_result.warnings)

        if moisture_eval.moisture_state == "SEVERE_DEFICIT":
            decision = "IRRIGATION_URGENT"
            reason = (
                f"Urgent irrigation required. The predicted 24-hour soil moisture ({predicted_moisture_24h:.1f}% VWC) "
                f"is dropping into critical deficit (severe stress line: {stress_threshold:.1f}% VWC), "
                f"risking severe crop moisture stress and potential yield loss."
            )
        elif moisture_eval.moisture_state == "DEFICIT":
            decision = "IRRIGATION_RECOMMENDED"
            reason = (
                f"Irrigation is recommended. The predicted 24-hour soil moisture ({predicted_moisture_24h:.1f}% VWC) "
                f"is expected to fall below the crop-specific allowable depletion threshold ({mad_threshold:.1f}% VWC)."
            )
        elif moisture_eval.moisture_state == "SAFE":
            # Check if approaching MAD threshold on a drying trajectory
            if predicted_moisture_24h <= (mad_threshold + monitor_buffer) and moisture_eval.moisture_delta_24h_vwc < 0:
                decision = "MONITOR"
                reason = (
                    f"Soil moisture is currently adequate ({current_moisture:.1f}% VWC), but is actively depleting "
                    f"and approaching the allowable depletion threshold ({mad_threshold:.1f}% VWC). "
                    "Monitor field conditions closely over the next 24 hours."
                )
            else:
                decision = "NO_IRRIGATION"
                reason = (
                    f"No irrigation is recommended right now. The predicted soil moisture for the upcoming 24 hours "
                    f"({predicted_moisture_24h:.1f}% VWC) remains comfortably above the allowable depletion threshold "
                    f"({mad_threshold:.1f}% VWC)."
                )
        else:  # HIGH or SATURATED
            decision = "NO_IRRIGATION"
            if moisture_eval.moisture_state == "SATURATED":
                reason = (
                    f"No irrigation is recommended. Soil moisture ({predicted_moisture_24h:.1f}% VWC) exceeds field capacity "
                    f"({fc:.1f}% VWC). Additional watering risks aeration stress and runoff."
                )
            else:
                reason = (
                    f"No irrigation is recommended right now. Soil moisture ({predicted_moisture_24h:.1f}% VWC) is ample "
                    f"and near field capacity ({fc:.1f}% VWC)."
                )

        # 7. Irrigation Method & Water Availability Context Modifiers
        is_water_limited = water_avail_str.lower() in ["low", "limited", "scarce", "poor"]
        if is_water_limited and decision in ["IRRIGATION_RECOMMENDED", "IRRIGATION_URGENT"]:
            reason += (
                " Note: Water availability is limited; prioritize watering during morning or evening hours "
                "to minimize evaporation, and consider targeted deficit irrigation."
            )

        if method_str.lower() in ["drip", "drip irrigation"]:
            method_guidance = " Localized drip application is recommended to maintain uniform root-zone hydration."
        elif method_str.lower() in ["sprinkler", "sprinklers"]:
            method_guidance = " Overhead sprinkler application recommended during low-wind periods to minimize evaporative drift."
        elif method_str.lower() in ["flood", "furrow"]:
            method_guidance = " Flood/furrow application recommended; ensure uniform water advance to avoid localized waterlogging."
        else:
            method_guidance = ""

        if method_guidance and decision in ["IRRIGATION_RECOMMENDED", "IRRIGATION_URGENT", "MONITOR"]:
            reason += method_guidance

        return {
            "decision": decision,
            "confidence": guardrail_result.confidence,
            "current_moisture": round(float(current_moisture), 2),
            "predicted_moisture_24h": round(float(predicted_moisture_24h), 2),
            "field_capacity": round(float(fc), 2),
            "mad_threshold": round(float(mad_threshold), 2),
            "depletion_fraction": round(float(moisture_eval.depletion_fraction), 4),
            "moisture_state": moisture_eval.moisture_state,
            "crop": canonical_crop_name,
            "crop_stage": stage_name,
            "dap": dap,
            "reason": reason,
            "domain_status": guardrail_result.domain_status,
            "warnings": warnings,
            "context": {
                "irrigation_method": method_str,
                "water_availability": water_avail_str,
                "farm_size": farm_size_str,
            },
        }


# Global singleton instance
adaptive_decision_engine = AdaptiveDecisionEngine()
