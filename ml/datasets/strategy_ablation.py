#!/usr/bin/env python3
"""
IrrigaSense — Controlled Feature Ablation Experiment (Milestone 7D)
===================================================================
Executes a strictly controlled, leakage-free feature ablation comparing:
  - Strategy A: Production-like features WITHOUT soil moisture
      [weather_temp, weather_humidity, weather_rain, weather_wind_speed, ph, hour]
  - Strategy B: Production-like features WITH soil moisture
      [weather_temp, weather_humidity, weather_rain, weather_wind_speed, ph, hour, soil_moisture]
  - Strategy A+ (Optional): Strategy A + weather_radiation
  - Strategy B+ (Optional): Strategy B + weather_radiation

Experimental Controls:
1. Target: target_mean_24h (identical to Milestone 7A and 7B).
2. Partitions:
     - Chronological Train: rows 0..32,904 (32,905 rows, 70%)
     - Chronological Validation: rows 32,905..39,955 (7,051 rows, 15%)
     - Chronological Test: rows 39,956..47,006 (7,051 rows, 15% — UNTOUCHED)
3. Model: Identical non-ANFIS baseline used in Milestone 7B:
     RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
4. Evaluation: MAE, RMSE, R² computed on Validation set (Global and Per-Zone).
5. Output:
     - CSV: ml/datasets/processed/strategy_ablation_results.csv
     - Verification SHA-256 to ensure master dataset remains unmodified.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Safe UTF-8 console output for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = SCRIPT_DIR / "processed"
DATASET_PATH = PROCESSED_DIR / "irrigation_anfis_dataset.csv"
SPLIT_INFO_PATH = PROCESSED_DIR / "dataset_split_info.json"
RESULTS_CSV_PATH = PROCESSED_DIR / "strategy_ablation_results.csv"

TARGET = "target_mean_24h"

# Strategy feature configurations
STRATEGIES: Dict[str, List[str]] = {
    "Strategy A (No Soil Moisture)": [
        "weather_temp",
        "weather_humidity",
        "weather_rain",
        "weather_wind_speed",
        "ph",
        "hour",
    ],
    "Strategy B (With Soil Moisture)": [
        "weather_temp",
        "weather_humidity",
        "weather_rain",
        "weather_wind_speed",
        "ph",
        "hour",
        "soil_moisture",
    ],
    "Strategy A+ (No SM + Radiation)": [
        "weather_temp",
        "weather_humidity",
        "weather_rain",
        "weather_wind_speed",
        "ph",
        "hour",
        "weather_radiation",
    ],
    "Strategy B+ (With SM + Radiation)": [
        "weather_temp",
        "weather_humidity",
        "weather_rain",
        "weather_wind_speed",
        "ph",
        "hour",
        "soil_moisture",
        "weather_radiation",
    ],
    "Milestone 7B Set C (Reference)": [
        "soil_moisture",
        "ec",
        "water_vol_past_4h",
        "weather_temp",
        "weather_radiation",
    ],
}


def compute_file_sha256(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def load_dataset_and_split() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    """Load dataset and extract chronological train and validation splits."""
    if not DATASET_PATH.is_file():
        raise FileNotFoundError(f"Master dataset not found at {DATASET_PATH}")
    if not SPLIT_INFO_PATH.is_file():
        raise FileNotFoundError(f"Split info not found at {SPLIT_INFO_PATH}")

    initial_hash = compute_file_sha256(DATASET_PATH)
    df = pd.read_csv(DATASET_PATH)

    with open(SPLIT_INFO_PATH, "r", encoding="utf-8") as f:
        split_meta = json.load(f)

    train_len = split_meta["partitions"]["train"]["row_count"]
    val_len = split_meta["partitions"]["validation"]["row_count"]

    assert len(df) == 47007, f"Expected 47,007 rows, found {len(df)}"
    assert train_len == 32905, f"Expected 32,905 train rows, found {train_len}"
    assert val_len == 7051, f"Expected 7,051 val rows, found {val_len}"

    train_df = df.iloc[:train_len].copy()
    val_df = df.iloc[train_len : train_len + val_len].copy()

    # Confirm test set (rows 39956..47006) remains 100% untouched
    test_len = split_meta["partitions"]["test"]["row_count"]
    assert train_len + val_len + test_len == len(df)

    return df, train_df, val_df, initial_hash


def evaluate_model(
    model: RandomForestRegressor,
    X_val: pd.DataFrame,
    y_val: pd.Series,
) -> Dict[str, float]:
    """Calculate MAE, RMSE, and R2."""
    preds = model.predict(X_val)
    mae = float(mean_absolute_error(y_val, preds))
    rmse = float(np.sqrt(mean_squared_error(y_val, preds)))
    r2 = float(r2_score(y_val, preds))
    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
    }


def run_ablation() -> Tuple[pd.DataFrame, Dict[str, Any]]:
    print("=" * 70)
    print("IRRIGASENSE — MILESTONE 7D: CONTROLLED FEATURE ABLATION EXPERIMENT")
    print("=" * 70)
    print(f"Master Dataset : {DATASET_PATH.name}")
    print(f"Target Feature : {TARGET}")
    print("Model Family   : RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)")
    print("-" * 70)

    df, train_df, val_df, initial_hash = load_dataset_and_split()
    print(f"Chronological Train Rows : {len(train_df):,} (70%)")
    print(f"Chronological Val Rows   : {len(val_df):,} (15%)")
    print(f"Chronological Test Rows  : {len(df) - len(train_df) - len(val_df):,} (15% — UNTOUCHED)")

    zone_labels = {
        1: "Zone 1 (Tomato, open field)",
        2: "Zone 2 (Tomato, open field)",
        3: "Zone 3 (Tomato, pots)",
        4: "Zone 4 (Zucchini)",
        5: "Zone 5 (Blueberry)",
    }

    # Discover zones with validation data
    val_zones = sorted(val_df["zone"].unique())
    print(f"\nZones present in Validation Partition: {[zone_labels[z] for z in val_zones]}")

    results_records: List[Dict[str, Any]] = []
    models: Dict[str, RandomForestRegressor] = {}

    print("\n--- [1] GLOBAL VALIDATION PERFORMANCE BY STRATEGY ---")
    for strat_name, features in STRATEGIES.items():
        print(f"\nTraining [{strat_name}] with {len(features)} features:")
        print(f"  Features: {', '.join(features)}")

        rf = RandomForestRegressor(
            n_estimators=100,
            max_depth=12,
            random_state=42,
            n_jobs=-1,
        )
        rf.fit(train_df[features], train_df[TARGET])
        models[strat_name] = rf

        # Global validation
        metrics = evaluate_model(rf, val_df[features], val_df[TARGET])
        print(f"  -> Validation MAE : {metrics['mae']:.4f}%")
        print(f"  -> Validation RMSE: {metrics['rmse']:.4f}%")
        print(f"  -> Validation R²  : {metrics['r2']:.4f}")

        results_records.append({
            "strategy": strat_name,
            "scope": "Global Validation",
            "zone_id": "All",
            "zone_label": "All Validation Sectors",
            "sample_count": len(val_df),
            "feature_count": len(features),
            "features_used": "; ".join(features),
            "mae": metrics["mae"],
            "rmse": metrics["rmse"],
            "r2": metrics["r2"],
        })

    print("\n--- [2] PER-ZONE VALIDATION PERFORMANCE ---")
    for zone_id in val_zones:
        z_val_df = val_df[val_df["zone"] == zone_id]
        z_label = zone_labels[zone_id]
        z_count = len(z_val_df)
        print(f"\n--- {z_label} (N = {z_count:,}) ---")

        for strat_name, features in STRATEGIES.items():
            rf = models[strat_name]
            z_metrics = evaluate_model(rf, z_val_df[features], z_val_df[TARGET])
            print(f"  {strat_name:35s} | MAE: {z_metrics['mae']:.4f}% | RMSE: {z_metrics['rmse']:.4f}% | R²: {z_metrics['r2']:.4f}")

            results_records.append({
                "strategy": strat_name,
                "scope": f"Per-Zone (Zone {zone_id})",
                "zone_id": zone_id,
                "zone_label": z_label,
                "sample_count": z_count,
                "feature_count": len(features),
                "features_used": "; ".join(features),
                "mae": z_metrics["mae"],
                "rmse": z_metrics["rmse"],
                "r2": z_metrics["r2"],
            })

    results_df = pd.DataFrame(results_records)
    results_df.to_csv(RESULTS_CSV_PATH, index=False)
    print(f"\n[OK] Strategy ablation CSV exported to: {RESULTS_CSV_PATH.name}")

    # Compute improvement metrics between Strategy A and Strategy B
    strat_a_global = results_df[(results_df["strategy"] == "Strategy A (No Soil Moisture)") & (results_df["scope"] == "Global Validation")].iloc[0]
    strat_b_global = results_df[(results_df["strategy"] == "Strategy B (With Soil Moisture)") & (results_df["scope"] == "Global Validation")].iloc[0]
    strat_bp_global = results_df[(results_df["strategy"] == "Strategy B+ (With SM + Radiation)") & (results_df["scope"] == "Global Validation")].iloc[0]

    abs_r2_diff = strat_b_global["r2"] - strat_a_global["r2"]
    rel_r2_diff = (abs_r2_diff / abs(strat_a_global["r2"])) * 100.0 if strat_a_global["r2"] != 0 else 0.0
    mae_reduction = strat_a_global["mae"] - strat_b_global["mae"]
    mae_reduction_pct = (mae_reduction / strat_a_global["mae"]) * 100.0
    rmse_reduction = strat_a_global["rmse"] - strat_b_global["rmse"]
    rmse_reduction_pct = (rmse_reduction / strat_a_global["rmse"]) * 100.0

    improvement_summary = {
        "strategy_a": {
            "mae": strat_a_global["mae"],
            "rmse": strat_a_global["rmse"],
            "r2": strat_a_global["r2"],
        },
        "strategy_b": {
            "mae": strat_b_global["mae"],
            "rmse": strat_b_global["rmse"],
            "r2": strat_b_global["r2"],
        },
        "strategy_b_plus": {
            "mae": strat_bp_global["mae"],
            "rmse": strat_bp_global["rmse"],
            "r2": strat_bp_global["r2"],
        },
        "improvements_b_vs_a": {
            "absolute_r2_improvement": round(abs_r2_diff, 4),
            "relative_r2_improvement_pct": round(rel_r2_diff, 2),
            "mae_reduction": round(mae_reduction, 4),
            "mae_reduction_pct": round(mae_reduction_pct, 2),
            "rmse_reduction": round(rmse_reduction, 4),
            "rmse_reduction_pct": round(rmse_reduction_pct, 2),
        },
    }

    print("\n--- [3] STRATEGY A vs STRATEGY B IMPROVEMENT DELTAS ---")
    print(f"  Absolute R² Improvement       : +{abs_r2_diff:.4f} (from {strat_a_global['r2']:.4f} to {strat_b_global['r2']:.4f})")
    print(f"  Relative R² Improvement       : +{rel_r2_diff:.2f}%")
    print(f"  MAE Reduction                 : -{mae_reduction:.4f}% ({mae_reduction_pct:.2f}% relative reduction)")
    print(f"  RMSE Reduction                : -{rmse_reduction:.4f}% ({rmse_reduction_pct:.2f}% relative reduction)")

    # Verify master dataset hash unchanged
    final_hash = compute_file_sha256(DATASET_PATH)
    assert initial_hash == final_hash, "CRITICAL ERROR: Master dataset was modified during ablation!"
    print(f"\n  [VERIFIED] Master dataset SHA-256 remains 100% UNTOUCHED:")
    print(f"             {final_hash}")

    print("\n" + "=" * 70)
    print("SUCCESS: MILESTONE 7D ABLATION EXPERIMENT COMPLETED CLEANLY!")
    print("=" * 70)

    return results_df, improvement_summary


if __name__ == "__main__":
    run_ablation()
