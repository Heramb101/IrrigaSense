#!/usr/bin/env python3
"""
IrrigaSense — Milestone 8D Test Suite: Final ANFIS Test Evaluation
=================================================================
Validates:
  1. Frozen model loads successfully.
  2. Model has exactly 5 inputs.
  3. Model has exactly 32 rules.
  4. Model has exactly 212 parameters.
  5. Test partition contains exactly 7,051 rows (indices 39,956..47,006).
  6. Test predictions contain no NaN or Inf.
  7. Computed test metrics are finite and well-defined.
  8. Master dataset hash remains 100% unchanged (fe11346d873d...).
  9. Model artifact remains readable and certified.
  10. Test evaluation does not modify model parameters.
  11. Integrity certificate and error extremes artifacts exist.
  12. All 6 diagnostic test figures exist and are non-empty.
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
FROZEN_MODEL_JSON = PROJECT_ROOT / "ml" / "anfis" / "artifacts" / "anfis_final_validation_best.json"

REPORT_MD = PROJECT_ROOT / "ml" / "anfis" / "reports" / "8D_final_test_evaluation.md"
INTEGRITY_JSON = PROJECT_ROOT / "ml" / "anfis" / "reports" / "8D_model_integrity.json"
EXTREMES_CSV = PROJECT_ROOT / "ml" / "anfis" / "reports" / "8D_error_extremes.csv"
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
        f"Master dataset hash changed! Expected {EXPECTED_MASTER_HASH}, got {sha256.hexdigest()}"
    )


def test_frozen_model_loads_successfully():
    """Verify frozen model artifact is readable and instantiates cleanly."""
    assert FROZEN_MODEL_JSON.exists(), "Frozen model JSON artifact missing!"
    model = ANFISModel.load_model(FROZEN_MODEL_JSON)
    assert model is not None
    assert isinstance(model, ANFISModel)


def test_model_inputs_and_features():
    """Verify model has exactly 5 inputs matching production specifications."""
    model = ANFISModel.load_model(FROZEN_MODEL_JSON)
    assert model.n_inputs == 5, f"Expected 5 inputs, got {model.n_inputs}"
    assert model.feature_names == EXPECTED_FEATURES
    assert model.target_name == EXPECTED_TARGET


def test_model_rules_and_parameters():
    """Verify model has exactly 32 rules and 212 parameters."""
    model = ANFISModel.load_model(FROZEN_MODEL_JSON)
    assert model.n_rules == 32, f"Expected 32 rules, got {model.n_rules}"
    assert model.total_premise_params == 20
    assert model.total_consequent_params == 192
    assert model.total_params == 212
    assert model.centers.shape == (5, 2)
    assert model.sigmas.shape == (5, 2)
    assert model.consequents.shape == (32, 6)


def test_test_partition_row_count():
    """Verify test partition contains exactly 7,051 rows (indices 39,956..47,006)."""
    assert DERIVED_CSV.exists(), "Derived training matrix missing!"
    df = pd.read_csv(DERIVED_CSV)
    test_rows = df[df["split"] == "test"]
    assert len(test_rows) == 7051, f"Expected 7,051 test rows, got {len(test_rows)}"
    assert test_rows.index[0] == 39956
    assert test_rows.index[-1] == 47006


def test_test_predictions_no_nan_or_inf():
    """Verify test predictions contain no NaN or Inf values."""
    model = ANFISModel.load_model(FROZEN_MODEL_JSON)
    df = pd.read_csv(DERIVED_CSV)
    test_df = df[df["split"] == "test"]

    with open(NORM_JSON, "r", encoding="utf-8") as f:
        norm = json.load(f)

    X_test_raw = test_df[EXPECTED_FEATURES].to_numpy(dtype=np.float64)
    X_test_norm = np.zeros_like(X_test_raw)
    for j, feat in enumerate(EXPECTED_FEATURES):
        fmin = norm["features"][feat]["train_min"]
        fmax = norm["features"][feat]["train_max"]
        X_test_norm[:, j] = (X_test_raw[:, j] - fmin) / (fmax - fmin)

    preds = model.predict(X_test_norm)
    assert len(preds) == 7051
    assert not np.isnan(preds).any(), "NaN found in test predictions!"
    assert not np.isinf(preds).any(), "Inf found in test predictions!"


def test_test_metrics_are_finite():
    """Verify all computed test metrics in the integrity report are finite numbers."""
    assert INTEGRITY_JSON.exists(), "8D_model_integrity.json missing!"
    with open(INTEGRITY_JSON, "r", encoding="utf-8") as f:
        integrity = json.load(f)

    raw_metrics = integrity["final_test_metrics_raw"]
    clipped_metrics = integrity["final_test_metrics_clipped"]

    for k, v in raw_metrics.items():
        assert np.isfinite(v), f"Raw metric {k} is not finite: {v}"

    for k, v in clipped_metrics.items():
        assert np.isfinite(v), f"Clipped metric {k} is not finite: {v}"

    assert integrity["final_verdict"] == "CONDITIONAL PASS"
    assert integrity["milestone_9_unlocked"] is True


def test_evaluation_does_not_modify_model_parameters():
    """Verify evaluating the model on test data causes zero parameter modification."""
    with open(FROZEN_MODEL_JSON, "r", encoding="utf-8") as f:
        d_before = json.load(f)

    model = ANFISModel.load_model(FROZEN_MODEL_JSON)
    c_before = model.centers.copy()
    s_before = model.sigmas.copy()
    p_before = model.consequents.copy()

    # Run inference on dummy and test data
    dummy_input = np.random.uniform(0.0, 1.0, size=(100, 5))
    _ = model.predict(dummy_input)

    np.testing.assert_array_equal(model.centers, c_before, err_msg="Centers were altered during inference!")
    np.testing.assert_array_equal(model.sigmas, s_before, err_msg="Sigmas were altered during inference!")
    np.testing.assert_array_equal(model.consequents, p_before, err_msg="Consequents were altered during inference!")


def test_artifacts_and_figures_exist():
    """Verify all required reports, figures, and CSVs exist and are non-empty."""
    assert REPORT_MD.exists(), "8D_final_test_evaluation.md missing!"
    assert REPORT_MD.stat().st_size > 5000, "Report is suspiciously small!"

    assert EXTREMES_CSV.exists(), "8D_error_extremes.csv missing!"
    df_ext = pd.read_csv(EXTREMES_CSV)
    assert len(df_ext) == 10, f"Expected 10 error extremes, got {len(df_ext)}"

    expected_figures = [
        "8d_predicted_vs_actual_test.png",
        "8d_test_residuals.png",
        "8d_test_residual_distribution.png",
        "8d_test_timeseries.png",
        "8d_test_error_distribution.png",
        "8d_test_error_by_target_range.png",
    ]
    for fig in expected_figures:
        fig_path = FIGURES_DIR / fig
        assert fig_path.exists(), f"Figure {fig} missing!"
        assert fig_path.stat().st_size > 10000, f"Figure {fig} too small (<10KB)!"
