#!/usr/bin/env python3
"""
IrrigaSense - Feature Parity Resolution & Training Matrix Pipeline (Milestone 8B)
================================================================================
Resolves the two identified training feature-parity gaps:
  1. et0_fao_evapotranspiration (mm/day) derived via FAO-56 Penman-Monteith
  2. clay_content (%) mapped from ISRIC SoilGrids and documented substrate records

Strict Governance:
  - Master dataset (ml/datasets/processed/irrigation_anfis_dataset.csv) remains IMMUTABLE.
  - Splits strictly preserved: Train=32,905, Val=7,051, Test=7,051 (Locked).
  - Derived matrix saved separately to: ml/datasets/processed/anfis_training/anfis_training_matrix.csv.
  - Normalization parameters fitted exclusively on the TRAINING partition and saved to:
    ml/anfis/artifacts/normalization.json.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd

# Safe UTF-8 console output for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
MASTER_CSV_PATH = PROJECT_ROOT / "ml" / "datasets" / "processed" / "irrigation_anfis_dataset.csv"
SPLIT_INFO_PATH = PROJECT_ROOT / "ml" / "datasets" / "processed" / "dataset_split_info.json"
OUTPUT_DIR = PROJECT_ROOT / "ml" / "datasets" / "processed" / "anfis_training"
OUTPUT_MATRIX_PATH = OUTPUT_DIR / "anfis_training_matrix.csv"
ARTIFACTS_DIR = SCRIPT_DIR / "artifacts"
NORMALIZATION_PATH = ARTIFACTS_DIR / "normalization.json"

EXPECTED_MASTER_HASH = "fe11346d873d65598ff37eeac2196da497c3ab82299b0f9f6be1356fd299b2c8"

# Site coordinates: Arnesano (Lecce, Apulia, Italy) - Università del Salento Experimental Station
SITE_LATITUDE_DEG = 40.3344
SITE_LONGITUDE_DEG = 18.0933
SITE_ELEVATION_M = 35.0

# Zone to Clay Content mapping:
# Source: ISRIC SoilGrids 1.0.0 WCS query (clay_0-5cm_mean) at Arnesano station coordinates (22.6% clay, sandy clay loam)
# and published agronomic setup (Adamo et al., 2026, Smart Agricultural Technology, Article 102558):
# - Zone 1 & 2: Tomato, open-field native soil -> 22.6%
# - Zone 3: Tomato, pots (soilless substrate: agriperlite & coconut fiber) -> 0.0% mineral clay
# - Zone 4: Zucchini, open-field native soil -> 22.6%
# - Zone 5: Blueberry, acidophilic organic peat substrate (mean pH 4.99) -> 0.0% mineral clay
ZONE_CLAY_MAP = {
    1: 22.6,
    2: 22.6,
    3: 0.0,
    4: 22.6,
    5: 0.0,
}


def verify_master_hash(file_path: Path, expected_hash: str) -> str:
    """Calculates SHA-256 hash of the master dataset and verifies immutability."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    digest = sha256.hexdigest()
    if digest != expected_hash:
        raise ValueError(
            f"MASTER DATASET INTEGRITY VIOLATION!\n"
            f"Expected SHA-256: {expected_hash}\n"
            f"Actual SHA-256:   {digest}"
        )
    return digest


def calculate_fao56_penman_monteith(df_weather: pd.DataFrame) -> pd.Series:
    """
    Calculates reference evapotranspiration (ET₀, mm/day) on a 10-minute grid
    using the standardized FAO-56 Penman-Monteith equation for short time steps.
    
    Equations & Steps:
      1. Atmospheric pressure P (kPa) from weather_pressure (hPa): P = hPa / 10
      2. Psychrometric constant gamma = 0.000665 * P (kPa / °C)
      3. Saturation vapor pressure e_s(T) and actual vapor pressure e_a = e_s * (RH/100) (kPa)
      4. Vapor pressure deficit VPD = max(0, e_s - e_a) (kPa)
      5. Slope of vapor pressure curve Delta = 4098 * e_s / (T + 237.3)^2 (kPa / °C)
      6. Wind speed at 2m height u2 = max(0.5, weather_wind_speed / 3.6) (m/s)
      7. Solar radiation energy rate: Rs_rate = weather_radiation * 0.0036 (MJ / (m² · hr))
      8. Extraterrestrial radiation Ra and clear-sky radiation Rso for local solar angle
      9. Net radiation Rn = Rns - Rnl and soil heat flux G = 0.1 Rn (day) or 0.5 Rn (night)
      10. Short time-step PM formula (Cn = 37, Cd = 0.34 day / 0.96 night) -> ET₀ rate (mm/hr)
      11. Step depth = ET₀ rate * (10 / 60) (mm per 10-min step)
      12. Rolling 24-hour backward sum (rolling('24h')) -> continuous physical ET₀ (mm/day)
          Zero future information leakage: only historical observations [t-24h, t] are used.
    """
    weather = df_weather.copy()
    weather["ts"] = pd.to_datetime(weather["ts"])
    weather = weather.sort_values("ts").reset_index(drop=True)

    lat_rad = np.radians(SITE_LATITUDE_DEG)
    elev_m = SITE_ELEVATION_M

    T = weather["weather_temp"]
    P = weather["weather_pressure"] / 10.0  # hPa to kPa
    gamma = 0.000665 * P

    e_s = 0.6108 * np.exp(17.27 * T / (T + 237.3))
    e_a = e_s * (weather["weather_humidity"] / 100.0)
    vpd = np.maximum(0.0, e_s - e_a)

    Delta = 4098.0 * e_s / ((T + 237.3) ** 2)
    u2 = np.maximum(0.5, weather["weather_wind_speed"] / 3.6)

    # 1 W/m² = 3600 J/(hr·m²) = 0.0036 MJ/(m²·hr)
    Rs_rate = weather["weather_radiation"] * 0.0036

    doy = weather["ts"].dt.dayofyear
    hour_float = weather["ts"].dt.hour + weather["ts"].dt.minute / 60.0

    delta_sol = 0.409 * np.sin(2.0 * np.pi * doy / 365.0 - 1.39)
    dr = 1.0 + 0.033 * np.cos(2.0 * np.pi * doy / 365.0)

    omega = (np.pi / 12.0) * (hour_float - 12.0)
    sin_beta = np.sin(lat_rad) * np.sin(delta_sol) + np.cos(lat_rad) * np.cos(delta_sol) * np.cos(omega)
    sin_beta = np.maximum(0.0, sin_beta)

    # Ra in MJ / (m² · hr): Gsc = 0.0820 MJ/(m²·min) -> 4.92 MJ/(m²·hr)
    Ra_hourly = np.where(sin_beta > 0, 4.92 * dr * sin_beta, 0.0)
    Rso_hourly = (0.75 + 2e-5 * elev_m) * Ra_hourly
    Rso_hourly = np.maximum(0.001, Rso_hourly)

    Rns = 0.77 * Rs_rate
    rel_rs = np.clip(Rs_rate / Rso_hourly, 0.3, 1.0)
    f_cd = np.where(Ra_hourly > 0.1, 1.35 * rel_rs - 0.35, 0.7)

    sigma_hourly = 2.043e-10  # 4.903e-9 / 24
    T_K = T + 273.16
    Rnl = sigma_hourly * (T_K ** 4) * (0.34 - 0.14 * np.sqrt(e_a)) * f_cd

    Rn = Rns - Rnl
    G = np.where(Rn >= 0, 0.1 * Rn, 0.5 * Rn)

    Cd = np.where(Rn >= 0, 0.34, 0.96)
    num = 0.408 * Delta * (Rn - G) + gamma * (37.0 / (T + 273.0)) * u2 * vpd
    denom = Delta + gamma * (1.0 + Cd * u2)

    et0_rate_mm_hr = np.maximum(0.0, num / denom)
    et0_step_mm = et0_rate_mm_hr * (10.0 / 60.0)

    weather["et0_step_mm"] = et0_step_mm
    weather_indexed = weather.set_index("ts")

    # Time-based rolling 24-hour backward sum
    et0_rolling_24h = weather_indexed["et0_step_mm"].rolling("24h").sum().reset_index(drop=True)
    return et0_rolling_24h


def build_derived_matrix() -> pd.DataFrame:
    """Ingests master dataset, computes features, validates, and exports derived matrix."""
    print("=" * 70)
    print("IRRIGASENSE — FEATURE PARITY RESOLUTION & MATRIX GENERATION (8B)")
    print("=" * 70)

    # 1. Verify Master Dataset Immutability
    print(f"Verifying Master CSV: {MASTER_CSV_PATH}")
    master_hash = verify_master_hash(MASTER_CSV_PATH, EXPECTED_MASTER_HASH)
    print(f"Master Dataset SHA-256 Verified: {master_hash} (IMMUTABLE)")

    # 2. Read Master Dataset (Read-Only)
    df = pd.read_csv(MASTER_CSV_PATH)
    total_rows = len(df)
    print(f"Master Dataset Records: {total_rows} rows")

    # 3. Read Split Information
    with open(SPLIT_INFO_PATH, "r") as f:
        split_info = json.load(f)
    train_count = split_info["partitions"]["train"]["row_count"]
    val_count = split_info["partitions"]["validation"]["row_count"]
    test_count = split_info["partitions"]["test"]["row_count"]

    assert total_rows == train_count + val_count + test_count, "Row count mismatch with split metadata!"
    print(f"Splits: Train={train_count}, Val={val_count}, Test={test_count} (Total={total_rows})")

    # Assign split labels chronologically
    split_labels = (
        ["train"] * train_count +
        ["val"] * val_count +
        ["test"] * test_count
    )

    # 4. Compute FAO-56 Penman-Monteith ET₀ on unique timestamps
    print("\nDeriving FAO-56 Penman-Monteith ET₀ (rolling 24h mm/day)...")
    unique_weather = df[[
        "ts", "weather_temp", "weather_humidity", "weather_wind_speed",
        "weather_radiation", "weather_pressure"
    ]].drop_duplicates("ts").sort_values("ts").reset_index(drop=True)

    unique_weather["et0_fao_evapotranspiration"] = calculate_fao56_penman_monteith(unique_weather)

    print(f"Unique meteorological timesteps: {len(unique_weather)}")
    print(f"ET₀ stats:\n{unique_weather['et0_fao_evapotranspiration'].describe()}")

    # Map ET₀ back to all rows via timestamp
    ts_to_et0 = dict(zip(unique_weather["ts"], unique_weather["et0_fao_evapotranspiration"]))
    et0_series = df["ts"].map(ts_to_et0)

    # 5. Map Clay Content via Documented Agronomic / SoilGrids Source
    print("\nMapping clay_content from ISRIC SoilGrids & documented agronomic zones...")
    clay_series = df["zone"].map(ZONE_CLAY_MAP)
    for z, c in ZONE_CLAY_MAP.items():
        z_count = (df["zone"] == z).sum()
        print(f"  Zone {z}: {c}% clay ({z_count} rows)")

    # 6. Construct Derived Matrix
    # Columns required:
    # 1. timestamp
    # 2. split
    # 3. soil_moisture_root_zone
    # 4. et0_fao_evapotranspiration
    # 5. temperature_2m
    # 6. relative_humidity_2m
    # 7. clay_content
    # 8. target_mean_24h
    derived_df = pd.DataFrame({
        "timestamp": df["ts"],
        "split": split_labels,
        "soil_moisture_root_zone": df["soil_moisture"].astype(float),
        "et0_fao_evapotranspiration": et0_series.astype(float),
        "temperature_2m": df["weather_temp"].astype(float),
        "relative_humidity_2m": df["weather_humidity"].astype(float),
        "clay_content": clay_series.astype(float),
        "target_mean_24h": df["target_mean_24h"].astype(float),
    })

    # 7. Comprehensive Derived Data Validation
    print("\nValidating Derived Matrix Integrity...")
    assert len(derived_df) == 47007, f"Row count {len(derived_df)} != 47007"
    assert derived_df.isnull().sum().sum() == 0, "Missing values detected in derived matrix!"
    assert derived_df["timestamp"].duplicated().sum() == df["ts"].duplicated().sum(), "Timestamp duplication altered!"
    assert list(derived_df.columns) == [
        "timestamp", "split", "soil_moisture_root_zone", "et0_fao_evapotranspiration",
        "temperature_2m", "relative_humidity_2m", "clay_content", "target_mean_24h"
    ], "Incorrect column specification!"

    # Verify split counts
    val_splits = derived_df["split"].value_counts()
    assert val_splits["train"] == train_count, f"Train count mismatch: {val_splits['train']} != {train_count}"
    assert val_splits["val"] == val_count, f"Val count mismatch: {val_splits['val']} != {val_count}"
    assert val_splits["test"] == test_count, f"Test count mismatch: {val_splits['test']} != {test_count}"

    print(f"Integrity check PASSED. Derived shape: {derived_df.shape}")

    # 8. Save Derived Training Matrix
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    derived_df.to_csv(OUTPUT_MATRIX_PATH, index=False)
    print(f"Exported derived matrix: {OUTPUT_MATRIX_PATH}")

    # Compute derived matrix SHA-256
    derived_hash = hashlib.sha256(open(OUTPUT_MATRIX_PATH, "rb").read()).hexdigest()
    print(f"Derived Matrix SHA-256: {derived_hash}")

    # 9. Fit Normalization Parameters on TRAINING PARTITION ONLY
    print("\nFitting Normalization Parameters on Chronological TRAINING Partition (rows 0..32,904)...")
    train_subset = derived_df[derived_df["split"] == "train"]
    feature_cols = [
        "soil_moisture_root_zone",
        "et0_fao_evapotranspiration",
        "temperature_2m",
        "relative_humidity_2m",
        "clay_content",
    ]

    normalization_dict: Dict[str, Any] = {
        "metadata": {
            "description": "ANFIS input normalization parameters fitted strictly on training partition.",
            "scaling_method": "min_max_scaling",
            "training_sample_count": len(train_subset),
            "source_derived_matrix_sha256": derived_hash,
            "formula": "x_norm = (x - min) / (max - min)",
            "target_normalized": False,
            "target_variable": "target_mean_24h",
            "target_unit": "% VWC",
        },
        "features": {},
    }

    for col in feature_cols:
        col_min = float(train_subset[col].min())
        col_max = float(train_subset[col].max())
        col_mean = float(train_subset[col].mean())
        col_std = float(train_subset[col].std())
        col_q25 = float(train_subset[col].quantile(0.25))
        col_q50 = float(train_subset[col].quantile(0.50))
        col_q75 = float(train_subset[col].quantile(0.75))

        units = {
            "soil_moisture_root_zone": "% VWC",
            "et0_fao_evapotranspiration": "mm/day",
            "temperature_2m": "°C",
            "relative_humidity_2m": "%",
            "clay_content": "%",
        }

        normalization_dict["features"][col] = {
            "unit": units[col],
            "train_min": col_min,
            "train_max": col_max,
            "train_mean": round(col_mean, 4),
            "train_std": round(col_std, 4),
            "train_q25": round(col_q25, 4),
            "train_q50": round(col_q50, 4),
            "train_q75": round(col_q75, 4),
            "transformed_range": [0.0, 1.0],
            "scale_factor": round(col_max - col_min, 6),
        }
        print(f"  {col}: min={col_min:.4f}, max={col_max:.4f}, mean={col_mean:.4f}, std={col_std:.4f}")

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(NORMALIZATION_PATH, "w") as f:
        json.dump(normalization_dict, f, indent=2)
    print(f"Exported normalization metadata: {NORMALIZATION_PATH}")

    # 10. Re-verify Master Dataset Immutability
    post_hash = verify_master_hash(MASTER_CSV_PATH, EXPECTED_MASTER_HASH)
    print(f"\nFinal Master Dataset SHA-256 Verification: {post_hash} (UNALTERED)")

    return derived_df


if __name__ == "__main__":
    build_derived_matrix()
