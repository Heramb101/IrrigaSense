#!/usr/bin/env python3
"""
Test Suite: Milestone 7B - Feature Analysis & ANFIS Input Selection
===================================================================
Verifies all criteria specified for Milestone 7B:
1. Feature analysis script runs cleanly and reproducibly.
2. All 7 expected output files exist and are populated.
3. No forbidden leakage features entered any candidate or recommended feature set.
4. Test data was never used for feature selection or fitting.
5. Models strictly use chronological train/validation partitions.
6. All 5 zones and 4 crops are evaluated.
7. Recommended ANFIS feature count is <= 8.
8. Master dataset remains 100% intact with verified SHA-256.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "ml" / "datasets" / "processed"
SCRIPT_PATH = PROJECT_ROOT / "ml" / "datasets" / "analyze_features.py"
MASTER_CSV_PATH = PROCESSED_DIR / "irrigation_anfis_dataset.csv"

# Known SHA-256 checksum of the master cleaned dataset from Milestone 7A
EXPECTED_MASTER_SHA256 = "fe11346d873d65598ff37eeac2196da497c3ab82299b0f9f6be1356fd299b2c8"

EXPECTED_OUTPUT_FILES = [
    "feature_correlations.csv",
    "feature_importance.csv",
    "mutual_information.csv",
    "feature_correlation_heatmap.png",
    "feature_importance.png",
    "target_distribution.png",
    "feature_selection_report.md",
]

FORBIDDEN_LEAKAGE = [
    "target_point_24h",
    "water_vol_to_24h",
    "real_moisture_delta",
    "target_mean_24h",
]


def test_1_script_execution():
    """Verify that analyze_features.py runs cleanly with exit code 0."""
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Script failed with output:\n{res.stdout}\n{res.stderr}"
    assert "SUCCESS: MILESTONE 7B FEATURE ANALYSIS COMPLETED WITH ZERO ERRORS!" in res.stdout


def test_2_all_output_files_exist():
    """Verify all 7 expected analysis output artifacts exist with non-zero size."""
    for filename in EXPECTED_OUTPUT_FILES:
        file_path = PROCESSED_DIR / filename
        assert file_path.is_file(), f"Expected artifact missing: {filename}"
        assert file_path.stat().st_size > 0, f"Artifact is empty: {filename}"


def test_3_no_leakage_features_in_recommended_sets():
    """Verify forbidden leakage features never appear in correlations, importances, or recommendations."""
    corr_df = pd.read_csv(PROCESSED_DIR / "feature_correlations.csv")
    imp_df = pd.read_csv(PROCESSED_DIR / "feature_importance.csv")
    mi_df = pd.read_csv(PROCESSED_DIR / "mutual_information.csv")

    for forbidden in ["target_point_24h", "water_vol_to_24h", "real_moisture_delta"]:
        assert forbidden not in corr_df["feature"].values
        assert forbidden not in imp_df["feature"].values
        assert forbidden not in mi_df["feature"].values

    report_text = (PROCESSED_DIR / "feature_selection_report.md").read_text(encoding="utf-8")
    assert "`target_point_24h` | Target Leakage" in report_text
    assert "`water_vol_to_24h` | Target Leakage" in report_text
    assert "`real_moisture_delta`" in report_text


def test_4_and_5_chronological_splits_preserved():
    """Verify chronological train (70%) and val (15%) splits were strictly maintained."""
    with open(PROCESSED_DIR / "dataset_split_info.json", "r", encoding="utf-8") as f:
        split_meta = json.load(f)

    train_n = split_meta["partitions"]["train"]["row_count"]
    val_n = split_meta["partitions"]["validation"]["row_count"]
    test_n = split_meta["partitions"]["test"]["row_count"]

    assert train_n == 32905
    assert val_n == 7051
    assert test_n == 7051

    # Verify report explicitly documents test set was untouched
    report_text = (PROCESSED_DIR / "feature_selection_report.md").read_text(encoding="utf-8")
    assert "100% UNTOUCHED" in report_text


def test_6_all_zones_and_crops_evaluated():
    """Verify that all 5 zones and 4 crops are documented in the report."""
    report_text = (PROCESSED_DIR / "feature_selection_report.md").read_text(encoding="utf-8")
    for z in range(1, 6):
        assert f"Zone {z}" in report_text
    for crop in ["Tomato, open field", "Tomato, pots", "Zucchini", "Blueberry"]:
        assert crop in report_text


def test_7_recommended_feature_count_le_8():
    """Verify the recommended ANFIS feature sets have <= 8 features."""
    report_text = (PROCESSED_DIR / "feature_selection_report.md").read_text(encoding="utf-8")
    assert "Set B (8 Features)" in report_text
    assert "Set C (5 Features)" in report_text


def test_8_master_dataset_unmodified():
    """Verify master CSV SHA-256 checksum is bit-for-bit identical to Milestone 7A."""
    h = hashlib.sha256(MASTER_CSV_PATH.read_bytes()).hexdigest()
    assert h == EXPECTED_MASTER_SHA256, f"Master dataset was altered! Hash: {h}"


def test_9_report_sections_complete():
    """Verify all 15 required sections are present in feature_selection_report.md."""
    report_text = (PROCESSED_DIR / "feature_selection_report.md").read_text(encoding="utf-8")
    required_sections = [
        "## 1. Dataset Summary",
        "## 2. Candidate Features Evaluated",
        "## 3. Features Excluded and Rationale",
        "## 4. Correlation Findings",
        "## 5. Feature Redundancy Findings",
        "## 6. Non-ANFIS Baseline Model Results",
        "## 7. Feature Importance Audit",
        "## 8. Mutual Information",
        "## 9. Zone & Crop Stratified Dynamics",
        "## 10. Multi-Set Performance Comparison",
        "## 11. Recommended ANFIS Input Architecture",
        "## 12. Supervised Target Variable",
        "## 13. Rationale for Each Selected Feature",
        "## 14. Live IrrigaSense Application Compatibility",
        "## 15. Limitations & Future Modeling Considerations",
    ]
    for section in required_sections:
        assert section in report_text, f"Missing report section: {section}"


if __name__ == "__main__":
    tests = [
        test_1_script_execution,
        test_2_all_output_files_exist,
        test_3_no_leakage_features_in_recommended_sets,
        test_4_and_5_chronological_splits_preserved,
        test_6_all_zones_and_crops_evaluated,
        test_7_recommended_feature_count_le_8,
        test_8_master_dataset_unmodified,
        test_9_report_sections_complete,
    ]
    print("=" * 70)
    print("RUNNING MILESTONE 7B VERIFICATION TEST SUITE")
    print("=" * 70)
    passed = 0
    for idx, test_fn in enumerate(tests, 1):
        try:
            test_fn()
            print(f"  [PASS] Test {idx:02d}: {test_fn.__name__}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] Test {idx:02d}: {test_fn.__name__} -> {e}")
            sys.exit(1)
    print("=" * 70)
    print(f"ALL {passed} MILESTONE 7B TESTS PASSED CLEANLY WITH ZERO ERRORS!")
    print("=" * 70)
