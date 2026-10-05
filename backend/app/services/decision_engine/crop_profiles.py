"""
IrrigaSense Decision Engine — Crop Agronomic Knowledge Layer
============================================================
Handles crop profile lookups, growth stage determination from Days After Planting (DAP),
and extraction of Managed Allowable Depletion (MAD) and soil threshold parameters.
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

def _find_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "ml" / "decision_engine" / "crop_profiles.json").exists():
            return parent
    return current.parents[4] if len(current.parents) >= 5 else current.parents[-1]

PROJECT_ROOT = _find_project_root()
PROFILES_PATH = PROJECT_ROOT / "ml" / "decision_engine" / "crop_profiles.json"



class CropProfileManager:
    """Manages crop profiles loaded from the agronomic knowledge base."""

    def __init__(self, profiles_path: Optional[Path] = None):
        self.profiles_path = profiles_path or PROFILES_PATH
        self.data: Dict[str, Any] = {}
        self.crops: Dict[str, Any] = {}
        self._load_profiles()

    def _load_profiles(self) -> None:
        """Loads and parses the crop profiles JSON file."""
        if not self.profiles_path.exists():
            raise FileNotFoundError(f"Crop profiles catalog not found at {self.profiles_path}")

        with open(self.profiles_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
            self.crops = self.data.get("crops", {})

    def get_crop_profile(self, crop_identifier: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Fuzzy/alias matching for crop name.
        Matches by crop_id, canonical crop_name, or aliases (case-insensitive).
        Returns the crop profile dictionary, or None if unrecognized.
        """
        if not crop_identifier:
            return None

        clean_query = str(crop_identifier).strip().lower()

        # Direct ID or name match
        for crop_id, profile in self.crops.items():
            if clean_query == crop_id.lower() or clean_query == profile.get("crop_name", "").lower():
                return profile

        # Alias match
        for _, profile in self.crops.items():
            aliases = profile.get("aliases", [])
            for alias in aliases:
                if clean_query == alias.lower() or alias.lower() in clean_query or clean_query in alias.lower():
                    return profile

        return None

    def calculate_dap_and_stage(
        self,
        crop_profile: Optional[Dict[str, Any]],
        planting_date: Union[date, str, datetime],
        current_date: Optional[Union[date, str, datetime]] = None,
    ) -> Tuple[int, str, str]:
        """
        Computes Days After Planting (DAP) and maps to configured FAO-56 crop stage.
        Returns: (dap, stage_key, human_readable_stage_name)
        """
        if current_date is None:
            today = date.today()
        elif isinstance(current_date, datetime):
            today = current_date.date()
        elif isinstance(current_date, str):
            today = datetime.strptime(current_date, "%Y-%m-%d").date()
        else:
            today = current_date

        if isinstance(planting_date, datetime):
            p_date = planting_date.date()
        elif isinstance(planting_date, str):
            # Parse ISO or YYYY-MM-DD
            p_date = datetime.strptime(planting_date[:10], "%Y-%m-%d").date()
        else:
            p_date = planting_date

        dap = (today - p_date).days

        if dap < 0:
            return dap, "pre_planting", "Pre-Planting (Future Date)"

        if not crop_profile or "growth_stages" not in crop_profile:
            return dap, "UNKNOWN", "Unknown Stage (Profile Unset)"

        stages = crop_profile["growth_stages"]
        total_dap = crop_profile.get("total_season_dap", 150)

        for stage_key, stage_info in stages.items():
            start = stage_info.get("dap_start", 0)
            end = stage_info.get("dap_end", 999)
            if start <= dap <= end:
                return dap, stage_key, stage_info.get("stage_name", stage_key.title())

        # If DAP exceeds configured season length, mark as Late-Season/Post-Harvest
        if dap > total_dap:
            return dap, "late_season", "Late-Season / Harvest / Post-Harvest"

        return dap, "mid_season", "Mid-Season (Fallback)"

    def get_crop_thresholds(
        self,
        crop_profile: Optional[Dict[str, Any]],
        is_soilless: bool = False,
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """
        Extracts (field_capacity_vwc, permanent_wilting_point_vwc, mad_fraction, stress_threshold_vwc)
        for the given crop and substrate setting.
        """
        if not crop_profile:
            return None, None, None, None

        mad_obj = crop_profile.get("mad", {})
        mad_fraction = mad_obj.get("fraction")

        soil_cat = "soilless_substrate" if is_soilless else "mineral_soil"
        soil_defaults = crop_profile.get("default_soil_thresholds", {}).get(soil_cat, {})

        fc = soil_defaults.get("field_capacity_vwc")
        pwp = soil_defaults.get("permanent_wilting_point_vwc")
        stress = soil_defaults.get("stress_threshold_vwc")

        # Validate that parameters are not marked as unverified
        if fc == "REQUIRES AGRONOMIC VALIDATION":
            fc = None
        if pwp == "REQUIRES AGRONOMIC VALIDATION":
            pwp = None
        if stress == "REQUIRES AGRONOMIC VALIDATION":
            stress = None

        return (
            float(fc) if fc is not None else None,
            float(pwp) if pwp is not None else None,
            float(mad_fraction) if mad_fraction is not None else None,
            float(stress) if stress is not None else None,
        )


# Global singleton instance
crop_profile_manager = CropProfileManager()
