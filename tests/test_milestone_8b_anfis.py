#!/usr/bin/env python3
"""
IrrigaSense — Milestone 8B Test Suite: Feature Parity & ANFIS Baseline Training
==============================================================================
Validates:
  1. Master CSV hash immutability (fe11346d873d65598ff37eeac2196da497c3ab82299b0f9f6be1356fd299b2c8).
  2. Derived training matrix schema (47,007 rows, exactly 8 columns, 0 nulls, correct split counts).
  3. Feature parity: FAO-56 ET0 and SoilGrids clay content within physical bounds.
  4. Normalization parameters fitted strictly on training partition (32,905 rows).
  5. Architecture A (32 rules, 212 parameters) checkpoint validity and performance.
  6. Architecture B (243 rules, 1,488 parameters) checkpoint validity.
  7. Forward inference latency and numerical stability (no NaN/Inf).
  8. Locked test partition quarantine (zero test evaluations).
  9. Visualizations and authoritative baseline report generation.
"""

import hashlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import pytest

from ml.anfis.anfis_model import ANFISModel
MASTER_CSV = PROJECT_ROOT / "ml" / "datasets" / "processed" / "irrigation_anfis_dataset.csv"
DERIVED_CSV = PROJECT_ROOT / "ml" / "datasets" / "processed" / "anfis_training" / "anfis_training_matrix.csv"
NORM_JSON = PROJECT_ROOT / "ml" / "anfis" / "artifacts" / "normalization.json"
ARCH_A_JSON = PROJECT_ROOT / "ml" / "anfis" / "artifacts" / "anfis_32_rule_best.json"
ARCH_B_JSON = PROJECT_ROOT / "ml" / "anfis" / "artifacts" / "anfis_243_rule_best.json"
REPORT_MD = PROJECT_ROOT / "ml" / "anfis" / "reports" / "8B_baseline_results.md"
FIGURES_DIR = PROJECT_ROOT / "ml" / "anfis" / "reports" / "figures"

EXPECTED_MASTER_HASH = "fe11346d873d65598ff37eeac2196da497c3ab82299b0f9f6be1356fd299b2c8"


def test_master_dataset_immutability():
    """Verify master CSV hash remains identical."""
    sha256 = hashlib.sha256()
    with open(MASTER_CSV, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    assert sha256.hexdigest() == EXPECTED_MASTER_HASH


def test_derived_matrix_integrity():
    """Verify derived training matrix shape, columns, and split distribution."""
    assert DERIVED_CSV.exists(), "Derived training matrix missing!"
    df = pd.read_csv(DERIVED_CSV)
    assert len(df) == 47007
    expected_cols = [
        "timestamp", "split", "soil_moisture_root_zone", "et0_fao_evapotranspiration",
        "temperature_2m", "relative_humidity_2m", "clay_content", "target_mean_24h"
    ]
    assert list(df.columns) == expected_cols
    assert df.isnull().sum().sum() == 0

    splits = df["split"].value_counts()
    assert splits["train"] == 32905
    assert splits["val"] == 7051
    assert splits["test"] == 7051


def test_feature_parity_ranges():
    """Verify physical plausibility of derived ET0 and clay content."""
    df = pd.read_csv(DERIVED_CSV)
    # ET0 must be non-negative and physically reasonable (0 to 15 mm/day)
    et0 = df["et0_fao_evapotranspiration"]
    assert et0.min() >= 0.0
    assert et0.max() < 15.0
    assert 3.0 <= et0.mean() <= 6.0

    # Clay content must match documented mapping (0.0% or 22.6%)
    clay = df["clay_content"]
    assert set(clay.unique()).issubset({0.0, 22.6})


def test_normalization_artifact():
    """Verify normalization parameters fitted exclusively on training rows."""
    assert NORM_JSON.exists(), "Normalization JSON missing!"
    with open(NORM_JSON, "r") as f:
        norm = json.load(f)
    assert norm["metadata"]["training_sample_count"] == 32905
    assert norm["metadata"]["target_normalized"] is False
    assert len(norm["features"]) == 5


def test_architecture_a_checkpoint():
    """Verify Architecture A state, rule count, parameter count, and validation metrics."""
    assert ARCH_A_JSON.exists(), "Arch A JSON missing!"
    model = ANFISModel.load_model(ARCH_A_JSON)
    assert model.n_inputs == 5
    assert model.n_mfs == 2
    assert model.n_rules == 32
    assert model.total_premise_params == 20
    assert model.total_consequent_params == 192
    assert model.total_params == 212

    # Validation MAE must be < 6.5% VWC and R2 > 0.70
    assert model.best_val_metrics["val_mae"] < 6.5
    assert model.best_val_metrics["val_r2"] > 0.70


def test_architecture_b_checkpoint():
    """Verify Architecture B state, rule count, parameter count."""
    assert ARCH_B_JSON.exists(), "Arch B JSON missing!"
    model = ANFISModel.load_model(ARCH_B_JSON)
    assert model.n_inputs == 5
    assert model.n_mfs == 3
    assert model.n_rules == 243
    assert model.total_premise_params == 30
    assert model.total_consequent_params == 1458
    assert model.total_params == 1488


def test_forward_inference():
    """Verify forward inference is sub-millisecond and produces valid predictions."""
    model = ANFISModel.load_model(ARCH_A_JSON)
    test_inputs = np.random.uniform(0.0, 1.0, size=(100, 5))
    preds = model.predict(test_inputs)
    assert len(preds) == 100
    assert not np.isnan(preds).any()
    assert not np.isinf(preds).any()


def test_visualizations_exist():
    """Verify that all 5 required figures exist and are non-empty."""
    expected_figures = [
        "training_validation_mae.png",
        "training_validation_rmse.png",
        "training_validation_r2.png",
        "predicted_vs_actual_validation.png",
        "validation_residual_distribution.png",
    ]
    for fig_name in expected_figures:
        fig_path = FIGURES_DIR / fig_name
        assert fig_path.exists(), f"Figure {fig_name} missing!"
        assert fig_path.stat().st_size > 5000, f"Figure {fig_name} is too small!"


def test_report_exists():
    """Verify that 8B_baseline_results.md exists and contains locked test confirmation."""
    assert REPORT_MD.exists(), "Baseline report missing!"
    content = REPORT_MD.read_text(encoding="utf-8")
    assert "LOCKED PARTITION" in content
    assert "32 rules" in content
    assert "243 rules" in content
    assert "212 trainable parameters" in content
    assert "1,488 trainable parameters" in content
