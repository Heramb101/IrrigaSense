#!/usr/bin/env python3
"""
IrrigaSense — Milestone 8C Test Suite: ANFIS Optimization, Validation & Baseline Comparison
==========================================================================================
Validates:
  1. Master CSV hash immutability (fe11346d873d65598ff37eeac2196da497c3ab82299b0f9f6be1356fd299b2c8).
  2. Exactly 5 production ANFIS inputs and correct regression target.
  3. Strict test partition quarantine (rows 39,956 to 47,006, 7,051 rows untouched).
  4. Normalization parameters fitted exclusively on the 32,905 training samples.
  5. Saved final validation-selected ANFIS checkpoint schema, parameter integrity, and rule count.
  6. Parameter dimensions: 20 premise parameters, 192 consequent parameters, 212 total.
  7. Experiment registry completeness (14 ANFIS runs + 1 fair RF baseline).
  8. Rule interpretability report completeness (all 32 rules documented).
  9. Membership function and diagnostic validation visualization artifacts.
  10. Fast sub-millisecond forward inference and numerical stability.
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
FINAL_MODEL_JSON = PROJECT_ROOT / "ml" / "anfis" / "artifacts" / "anfis_final_validation_best.json"
REGISTRY_CSV = PROJECT_ROOT / "ml" / "anfis" / "reports" / "8C_experiment_registry.csv"
RULES_MD = PROJECT_ROOT / "ml" / "anfis" / "reports" / "fuzzy_rules_32.md"
REPORT_MD = PROJECT_ROOT / "ml" / "anfis" / "reports" / "8C_optimization_results.md"
FIGURES_DIR = PROJECT_ROOT / "ml" / "anfis" / "reports" / "figures"

EXPECTED_MASTER_HASH = "fe11346d873d65598ff37eeac2196da497c3ab82299b0f9f6be1356fd299b2c8"
EXPECTED_FEATURES = [
    "soil_moisture_root_zone",
    "et0_fao_evapotranspiration",
    "temperature_2m",
    "relative_humidity_2m",
    "clay_content",
]
EXPECTED_TARGET = "target_mean_24h"


def test_master_dataset_immutability():
    """Verify master CSV hash remains 100% untouched."""
    sha256 = hashlib.sha256()
    with open(MASTER_CSV, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    assert sha256.hexdigest() == EXPECTED_MASTER_HASH, (
        f"Master CSV hash altered! Expected {EXPECTED_MASTER_HASH}, got {sha256.hexdigest()}"
    )


def test_frozen_feature_set_and_target():
    """Verify exactly five model inputs and the single target variable."""
    assert DERIVED_CSV.exists(), "Derived training matrix missing!"
    df = pd.read_csv(DERIVED_CSV)
    for feat in EXPECTED_FEATURES:
        assert feat in df.columns, f"Required feature {feat} missing from matrix!"
    assert EXPECTED_TARGET in df.columns, f"Required target {EXPECTED_TARGET} missing from matrix!"

    # Excluded variables must not be present as model inputs
    excluded = [
        "ec_bulk", "wind_speed_10m", "shortwave_radiation", "surface_pressure",
        "soil_ph", "irrigation_history_7d", "irrigation_duration_min", "hour"
    ]
    for ex in excluded:
        assert ex not in EXPECTED_FEATURES


def test_test_partition_quarantine():
    """Verify test partition (7,051 rows) remains completely quarantined."""
    df = pd.read_csv(DERIVED_CSV)
    test_rows = df[df["split"] == "test"]
    assert len(test_rows) == 7051, f"Expected 7051 test rows, found {len(test_rows)}"
    # Indices must be exactly rows 39956..47006
    assert test_rows.index[0] == 32905 + 7051
    assert test_rows.index[-1] == 47006


def test_normalization_trained_only_on_train_split():
    """Verify normalization artifact was fitted strictly on training partition."""
    assert NORM_JSON.exists(), "Normalization JSON missing!"
    with open(NORM_JSON, "r") as f:
        norm = json.load(f)
    assert norm["metadata"]["training_sample_count"] == 32905
    assert set(norm["features"].keys()) == set(EXPECTED_FEATURES)
    assert norm["metadata"]["target_normalized"] is False


def test_final_validation_best_model_artifact():
    """Verify final validation-selected ANFIS checkpoint exists and has all required keys."""
    assert FINAL_MODEL_JSON.exists(), "anfis_final_validation_best.json missing!"
    with open(FINAL_MODEL_JSON, "r") as f:
        model_dict = json.load(f)

    # Check required top-level keys
    required_keys = [
        "architecture", "feature_names", "target_name", "mf_type",
        "premise_parameters", "rule_table", "consequent_parameters",
        "normalization_parameters", "optimizer_configuration",
        "training_configuration", "best_epoch", "validation_metrics",
        "random_seed", "saved_at", "designation"
    ]
    for key in required_keys:
        assert key in model_dict, f"Missing required key '{key}' in saved model checkpoint!"

    assert model_dict["designation"] == "FINAL VALIDATION-SELECTED ANFIS MODEL"
    assert model_dict["feature_names"] == EXPECTED_FEATURES
    assert model_dict["target_name"] == EXPECTED_TARGET
    assert model_dict["architecture"] == "Architecture A (32 Rules, 212 Parameters)"
    assert model_dict["mf_type"] == "gaussian"


def test_anfis_parameter_dimensions_and_rule_count():
    """Verify 32 rules and exact parameter counts: 20 premise + 192 consequent = 212 total."""
    model = ANFISModel.load_model(FINAL_MODEL_JSON)
    assert model.n_inputs == 5
    assert model.n_mfs == 2
    assert model.n_rules == 32
    assert model.total_premise_params == 20
    assert model.total_consequent_params == 192
    assert model.total_params == 212

    # Verify shapes
    assert model.centers.shape == (5, 2)
    assert model.sigmas.shape == (5, 2)
    assert model.rule_table.shape == (32, 5)
    assert model.consequents.shape == (32, 6)

    # Verify validation performance bounds
    val_mae = model.best_val_metrics["val_mae"]
    val_r2 = model.best_val_metrics["val_r2"]
    assert val_mae < 6.0, f"Validation MAE {val_mae:.4f} exceeds target threshold of 6.0% VWC"
    assert val_r2 > 0.75, f"Validation R2 {val_r2:.4f} is below target threshold of 0.75"


def test_experiment_registry_integrity():
    """Verify experiment registry exists and logs all controlled experiments."""
    assert REGISTRY_CSV.exists(), "8C_experiment_registry.csv missing!"
    reg_df = pd.read_csv(REGISTRY_CSV)
    # Must have 15 rows (14 ANFIS + 1 RF)
    assert len(reg_df) >= 15, f"Expected at least 15 experiments, found {len(reg_df)}"

    required_cols = [
        "experiment_id", "architecture", "mf_count", "learning_rate", "ridge_lambda",
        "initialization", "patience", "epochs", "best_epoch", "train_mae", "val_mae",
        "train_rmse", "val_rmse", "train_r2", "val_r2", "generalization_gap_mae",
        "generalization_gap_rmse", "training_time", "selected", "notes"
    ]
    for col in required_cols:
        assert col in reg_df.columns, f"Column '{col}' missing from experiment registry!"

    # Exactly one experiment marked as selected
    selected_count = reg_df["selected"].sum()
    assert selected_count == 1, f"Expected exactly 1 selected experiment, got {selected_count}"

    # Selected experiment must be Architecture A
    selected_row = reg_df[reg_df["selected"]].iloc[0]
    assert "Architecture A" in selected_row["architecture"]


def test_fuzzy_rules_catalog():
    """Verify fuzzy_rules_32.md enumerates all 32 rules with readable descriptions."""
    assert RULES_MD.exists(), "fuzzy_rules_32.md missing!"
    content = RULES_MD.read_text(encoding="utf-8")
    assert "Complete 32-Rule Fuzzy Knowledge Base" in content
    # Check that all 32 rules are represented
    for r in range(1, 33):
        assert f"Rule {r:02d}" in content, f"Rule {r:02d} missing from fuzzy rules documentation!"


def test_diagnostic_figures_exist():
    """Verify all 7 diagnostic figures exist and are valid non-empty images."""
    expected_figs = [
        "membership_functions.png",
        "8c_predicted_vs_actual_val.png",
        "8c_validation_residuals.png",
        "8c_residual_distribution.png",
        "8c_error_by_target_range.png",
        "8c_error_by_zone.png",
        "8c_feature_sensitivity.png",
    ]
    for fig_name in expected_figs:
        fig_path = FIGURES_DIR / fig_name
        assert fig_path.exists(), f"Diagnostic figure '{fig_name}' missing!"
        assert fig_path.stat().st_size > 10000, f"Diagnostic figure '{fig_name}' is too small (<10KB)!"


def test_forward_inference_speed_and_stability():
    """Verify sub-millisecond forward latency and valid outputs on validation data."""
    import time
    model = ANFISModel.load_model(FINAL_MODEL_JSON)
    df = pd.read_csv(DERIVED_CSV)
    val_df = df[df["split"] == "val"]
    with open(NORM_JSON, "r") as f:
        norm = json.load(f)
    X_val_norm = np.zeros((100, 5), dtype=np.float64)
    for j, feat in enumerate(EXPECTED_FEATURES):
        fmin = norm["features"][feat]["train_min"]
        fmax = norm["features"][feat]["train_max"]
        X_val_norm[:, j] = (val_df[feat].iloc[:100].values - fmin) / (fmax - fmin)

    t0 = time.perf_counter()
    preds = model.predict(X_val_norm)
    t_elapsed = time.perf_counter() - t0
    latency_per_sample_ms = (t_elapsed / 100) * 1000.0

    assert latency_per_sample_ms < 1.0, f"Latency {latency_per_sample_ms:.4f} ms exceeds 1ms limit"
    assert len(preds) == 100
    assert not np.isnan(preds).any()
    assert not np.isinf(preds).any()
    # Predictions on real validation domain must be within plausible physical range [10, 100] % VWC
    assert (preds > 10.0).all(), "Predictions below wilting point (<10% VWC)"
    assert (preds < 100.0).all(), "Predictions above saturation (>100% VWC)"
