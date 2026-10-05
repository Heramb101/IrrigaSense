#!/usr/bin/env python3
"""
Test Suite: Milestone 7A - ANFIS Dataset Preparation & Validation
=================================================================
Verifies all 11 criteria specified for Milestone 7A:
1. Processing script runs cleanly and reproducibly.
2. Output CSV exists.
3. Validation report exists.
4. Split metadata exists.
5. All 5 zones are represented.
6. All 5 official crop mappings are represented.
7. target_mean_24h exists as target.
8. target_mean_24h is not used as an input feature.
9. No future-looking columns (target_point_24h, water_vol_to_24h, real_moisture_delta) are present.
10. Original 5 raw CSV files were not modified (SHA-256 integrity).
11. Clean sensor bounds (EC: 0-1000, pH: 3-9, 0 NaNs).
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
import pandas as pd
try:
    import pytest
except ImportError:
    pytest = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "ml" / "datasets" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "ml" / "datasets" / "processed"
SCRIPT_PATH = PROJECT_ROOT / "ml" / "datasets" / "process_dataset.py"

# Known baseline SHA-256 checksums of raw CSV files to guarantee zero modification
EXPECTED_RAW_SHA256 = {
    1: "e3c8ce709e89d1a7944bfbcfc0120a2f0166b4198cdf390efad659fd3acb9a89",
    2: "7436f9d1b03da0dd4a76cf2005e9ded38881d88d6b85c7f20cf7a3dc561ee5ac",
    3: "cc8b6e1e1609f5c749e0e3d05a4b5b237fc4cc79f38e1035d564ea3aabe09424",
    4: "166d58fbf442a0656621923c5c47c8495a4a19ad362be9daa0b83ccbfaa3ebfe",
    5: "305260f0d48a121a1f145fba772a2546df950af0aa8c74c87f526ecc3dc91f4e",
}

EXPECTED_COLUMNS = [
    "zone",
    "crop",
    "ts",
    "weather_temp",
    "weather_humidity",
    "weather_rain",
    "weather_pressure",
    "weather_wind_speed",
    "weather_radiation",
    "soil_temperature_0-7cm",
    "soil_temperature_7-18cm",
    "ec",
    "ph",
    "soil_moisture",
    "irrigation_duration_minutes",
    "water_vol_past_4h",
    "hour",
    "target_mean_24h",
]

PROHIBITED_LEAKAGE_COLUMNS = [
    "target_point_24h",
    "water_vol_to_24h",
    "real_moisture_delta",
]


def test_1_script_execution():
    """Verify that process_dataset.py runs cleanly with exit code 0."""
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Script failed with output:\n{res.stdout}\n{res.stderr}"
    assert "SUCCESS: MILESTONE 7A DATASET PREPARATION COMPLETED!" in res.stdout


def test_2_output_csv_exists_and_valid():
    """Verify that irrigation_anfis_dataset.csv exists and has correct dimensions."""
    csv_file = PROCESSED_DIR / "irrigation_anfis_dataset.csv"
    assert csv_file.is_file(), "Processed CSV file not found"
    
    df = pd.read_csv(csv_file)
    assert len(df) == 47007, f"Expected 47,007 rows, found {len(df)}"
    assert list(df.columns) == EXPECTED_COLUMNS, f"Columns mismatch: {list(df.columns)}"


def test_3_validation_report_exists_and_complete():
    """Verify that dataset_validation_report.md exists and contains all required items."""
    report_file = PROCESSED_DIR / "dataset_validation_report.md"
    assert report_file.is_file(), "Validation report file not found"
    
    content = report_file.read_text(encoding="utf-8")
    assert "Zone Row Counts (Original vs. Cleaned)" in content
    assert "Cleaning & Sensor Anomaly Audit" in content
    assert "Missing Value Audit" in content
    assert "Numeric Feature & Target Statistical Summary" in content
    assert "Time-Series Chronological Split Plan" in content
    assert "Data Integrity & Leakage Verification" in content
    assert "47,007" in content


def test_4_split_metadata_exists_and_valid():
    """Verify that dataset_split_info.json exists and enforces 70/15/15 split."""
    split_file = PROCESSED_DIR / "dataset_split_info.json"
    assert split_file.is_file(), "Split info JSON not found"
    
    with open(split_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["total_rows"] == 47007
    assert data["partitions"]["train"]["row_count"] == 32905
    assert data["partitions"]["validation"]["row_count"] == 7051
    assert data["partitions"]["test"]["row_count"] == 7051
    assert data["partitions"]["train"]["percentage"] == 70.0
    assert data["partitions"]["validation"]["percentage"] == 15.0
    assert data["partitions"]["test"]["percentage"] == 15.0


def test_5_all_five_zones_represented():
    """Verify that all five experimental zones (1 through 5) are represented."""
    df = pd.read_csv(PROCESSED_DIR / "irrigation_anfis_dataset.csv")
    unique_zones = sorted(df["zone"].unique().tolist())
    assert unique_zones == [1, 2, 3, 4, 5], f"Expected zones [1..5], found {unique_zones}"
    
    counts = df["zone"].value_counts().to_dict()
    assert counts[1] == 9531
    assert counts[2] == 11929
    assert counts[3] == 1090
    assert counts[4] == 12676
    assert counts[5] == 11781


def test_6_all_crop_labels_represented():
    """Verify that all official crop labels are mapped accurately to their zones."""
    df = pd.read_csv(PROCESSED_DIR / "irrigation_anfis_dataset.csv")
    crop_counts = df["crop"].value_counts().to_dict()
    
    expected_crops = {
        "Tomato, open field": 21460,  # Zone 1 (9531) + Zone 2 (11929)
        "Zucchini": 12676,            # Zone 4
        "Blueberry": 11781,           # Zone 5
        "Tomato, pots": 1090,         # Zone 3
    }
    assert crop_counts == expected_crops, f"Crop distribution mismatch: {crop_counts}"


def test_7_target_mean_24h_exists():
    """Verify that target_mean_24h is present as the primary target."""
    df = pd.read_csv(PROCESSED_DIR / "irrigation_anfis_dataset.csv")
    assert "target_mean_24h" in df.columns
    assert df["target_mean_24h"].isna().sum() == 0


def test_8_and_9_no_leakage_columns_in_dataset():
    """Verify that no future-looking columns appear in the dataset."""
    df = pd.read_csv(PROCESSED_DIR / "irrigation_anfis_dataset.csv")
    for col in PROHIBITED_LEAKAGE_COLUMNS:
        assert col not in df.columns, f"Prohibited leakage column found: {col}"


def test_10_raw_files_unmodified():
    """Verify that none of the original 5 raw CSV files were altered."""
    for zone_id, expected_hash in EXPECTED_RAW_SHA256.items():
        file_path = RAW_DIR / f"dataset_zone_{zone_id}_preprocessed.csv"
        assert file_path.is_file(), f"Raw file missing: {file_path}"
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Zone {zone_id} raw CSV file was modified!"


def test_11_sensor_data_bounds_and_completeness():
    """Verify physical cleaning bounds (EC 0-1000, pH 3-9, 0 missing)."""
    df = pd.read_csv(PROCESSED_DIR / "irrigation_anfis_dataset.csv")
    assert (df["ec"] >= 0).all() and (df["ec"] <= 1000).all(), "EC values out of [0, 1000] range"
    assert (df["ph"] >= 3.0).all() and (df["ph"] <= 9.0).all(), "pH values out of [3.0, 9.0] range"
    assert df.isna().sum().sum() == 0, "Missing values found in processed dataset"
    assert df.duplicated().sum() == 0, "Duplicate rows found in processed dataset"


if __name__ == "__main__":
    test_funcs = [
        test_1_script_execution,
        test_2_output_csv_exists_and_valid,
        test_3_validation_report_exists_and_complete,
        test_4_split_metadata_exists_and_valid,
        test_5_all_five_zones_represented,
        test_6_all_crop_labels_represented,
        test_7_target_mean_24h_exists,
        test_8_and_9_no_leakage_columns_in_dataset,
        test_10_raw_files_unmodified,
        test_11_sensor_data_bounds_and_completeness,
    ]
    print("=" * 70)
    print("RUNNING MILESTONE 7A DATASET VERIFICATION SUITE")
    print("=" * 70)
    passed = 0
    for idx, fn in enumerate(test_funcs, 1):
        try:
            fn()
            print(f"  [PASS] Test {idx:02d}: {fn.__name__}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] Test {idx:02d}: {fn.__name__} -> {e}")
            sys.exit(1)
    print("=" * 70)
    print(f"ALL {passed} TESTS PASSED CLEANLY WITH ZERO ERRORS!")
    print("=" * 70)
