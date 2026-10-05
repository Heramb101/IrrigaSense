"""
IrrigaSense Decision Engine — Frozen ANFIS Inference Service
============================================================
Loads and manages inference for the frozen ANFIS neural-fuzzy model
(Architecture A: 5 inputs, 2 MFs/input, 32 rules, 212 parameters).

Strict Production Feature Order:
  1. soil_moisture_root_zone     (% VWC)
  2. et0_fao_evapotranspiration  (mm/day)
  3. temperature_2m              (°C)
  4. relative_humidity_2m        (%)
  5. clay_content                (%)

Target:
  predicted_target_mean_24h      (% VWC)

NOTE: This service strictly performs forward-pass evaluation using the frozen
checkpoint. It does NOT train, backpropagate, or alter any model parameters.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger("irrigasense.anfis_inference")

# Dynamic project root discovery ensuring ml.* is importable from any working directory
def _resolve_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "ml" / "anfis" / "artifacts" / "anfis_final_validation_best.json").exists():
            return parent
    return current.parents[3] if len(current.parents) >= 4 else current.parents[-1]

PROJECT_ROOT = _resolve_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Backend directory also in sys.path
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

MODEL_PATH = PROJECT_ROOT / "ml" / "anfis" / "artifacts" / "anfis_final_validation_best.json"
NORM_PATH = PROJECT_ROOT / "ml" / "anfis" / "artifacts" / "normalization.json"

FEATURE_NAMES = [
    "soil_moisture_root_zone",
    "et0_fao_evapotranspiration",
    "temperature_2m",
    "relative_humidity_2m",
    "clay_content",
]


class ANFISInferenceService:
    """Singleton-style production inference runner for the frozen ANFIS model."""

    def __init__(self, model_path: Optional[Path] = None, norm_path: Optional[Path] = None):
        self.model_path = model_path or MODEL_PATH
        self.norm_path = norm_path or NORM_PATH
        self._model = None
        self._norm_params = None

    def _ensure_loaded(self) -> None:
        """Loads model weights and normalization parameters once into memory."""
        if self._model is not None and self._norm_params is not None:
            return

        from ml.anfis.anfis_model import ANFISModel

        if not self.model_path.exists():
            raise FileNotFoundError(f"Frozen ANFIS checkpoint not found at {self.model_path}")
        if not self.norm_path.exists():
            raise FileNotFoundError(f"Normalization parameters not found at {self.norm_path}")

        logger.info("Loading frozen ANFIS model checkpoint from %s", self.model_path)
        self._model = ANFISModel.load_model(self.model_path)

        with open(self.norm_path, "r", encoding="utf-8") as f:
            self._norm_params = json.load(f)

        logger.info("Frozen ANFIS model and normalization parameters loaded successfully.")

    def check_input_availability(
        self,
        soil_moisture_root_zone: Optional[float],
        et0_fao_evapotranspiration: Optional[float],
        temperature_2m: Optional[float],
        relative_humidity_2m: Optional[float],
        clay_content: Optional[float],
    ) -> Dict[str, bool]:
        """Returns presence status of each required ANFIS input for safe logging."""
        status = {
            "soil_moisture_root_zone": soil_moisture_root_zone is not None,
            "et0_fao_evapotranspiration": et0_fao_evapotranspiration is not None,
            "temperature_2m": temperature_2m is not None,
            "relative_humidity_2m": relative_humidity_2m is not None,
            "clay_content": clay_content is not None,
        }
        return status

    def predict_24h_soil_moisture(
        self,
        soil_moisture_root_zone: Optional[float],
        et0_fao_evapotranspiration: Optional[float],
        temperature_2m: Optional[float],
        relative_humidity_2m: Optional[float],
        clay_content: Optional[float],
    ) -> Optional[float]:
        """
        Runs one-shot forward inference using the frozen ANFIS model.

        Parameters:
            soil_moisture_root_zone: Volumetric water content in root zone (% VWC)
            et0_fao_evapotranspiration: Reference evapotranspiration (mm/day)
            temperature_2m: Air temperature (°C)
            relative_humidity_2m: Relative humidity (%)
            clay_content: Soil clay percentage (%)

        Returns:
            predicted_target_mean_24h: Predicted 24-hour mean moisture (% VWC),
            or None if any input is missing.
        """
        availability = self.check_input_availability(
            soil_moisture_root_zone,
            et0_fao_evapotranspiration,
            temperature_2m,
            relative_humidity_2m,
            clay_content,
        )

        logger.info(
            "ANFIS input telemetry availability: "
            "soil_moisture=%s, ET0=%s, temp=%s, RH=%s, clay=%s",
            "present" if availability["soil_moisture_root_zone"] else "MISSING",
            "present" if availability["et0_fao_evapotranspiration"] else "MISSING",
            "present" if availability["temperature_2m"] else "MISSING",
            "present" if availability["relative_humidity_2m"] else "MISSING",
            "present" if availability["clay_content"] else "MISSING",
        )

        if not all(availability.values()):
            missing_names = [k for k, v in availability.items() if not v]
            logger.warning(
                "ANFIS prediction cannot be generated: missing inputs (%s)",
                ", ".join(missing_names),
            )
            return None

        self._ensure_loaded()

        raw_features = [
            ("soil_moisture_root_zone", float(soil_moisture_root_zone)),
            ("et0_fao_evapotranspiration", float(et0_fao_evapotranspiration)),
            ("temperature_2m", float(temperature_2m)),
            ("relative_humidity_2m", float(relative_humidity_2m)),
            ("clay_content", float(clay_content)),
        ]

        # Min-max normalization strictly matching training partition parameters
        x_norm = np.zeros((1, 5), dtype=np.float64)
        for j, (fname, raw_val) in enumerate(raw_features):
            feat_meta = self._norm_params["features"][fname]
            fmin = feat_meta["train_min"]
            fmax = feat_meta["train_max"]
            x_norm[0, j] = (raw_val - fmin) / (fmax - fmin)

        predictions = self._model.predict(x_norm)
        predicted_scalar = round(float(predictions[0]), 2)

        logger.info(
            "ANFIS prediction generated: yes | predicted_target_mean_24h = %.2f%% VWC",
            predicted_scalar,
        )
        return predicted_scalar


# Global service instance for reuse across requests
anfis_inference_service = ANFISInferenceService()
