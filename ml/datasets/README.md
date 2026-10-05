# IrrigaSense Datasets & ML Data Pipeline

## Directory Structure

```
ml/datasets/
├── Crop_recommendation.csv                  # Baseline agricultural reference dataset
├── DATA_DICTIONARY.md                       # Authoritative dataset column specifications
├── README.md                                # Overview and pipeline documentation
├── process_dataset.py                       # Reproducible data ingestion & cleaning script
├── raw/                                     # Immutable source datasets
│   ├── dataset_zone_1_preprocessed.csv      # Zone 1 (Tomato, open field)
│   ├── dataset_zone_2_preprocessed.csv      # Zone 2 (Tomato, open field)
│   ├── dataset_zone_3_preprocessed.csv      # Zone 3 (Tomato, pots)
│   ├── dataset_zone_4_preprocessed.csv      # Zone 4 (Zucchini)
│   └── dataset_zone_5_preprocessed.csv      # Zone 5 (Blueberry)
└── processed/                               # Cleaned, validated modeling assets
    ├── irrigation_anfis_dataset.csv         # Combined ANFIS modeling dataset
    ├── dataset_validation_report.md         # Comprehensive 17-point validation audit
    └── dataset_split_info.json              # Chronological train/validation/test split metadata
```

## How to Regenerate the Processed Dataset

From the project root:

```powershell
python ml/datasets/process_dataset.py
```

This script:
1. Ingests all 5 raw zone datasets from `ml/datasets/raw/`.
2. Applies sensor bounds cleaning (`0 <= ec <= 1000`, `3 <= ph <= 9`, non-null targets).
3. Attaches official `zone` and `crop` attributes.
4. Enforces strict feature leakage prevention (excludes `target_point_24h`, `water_vol_to_24h`, `real_moisture_delta`).
5. Generates the 18-column combined modeling dataset: `ml/datasets/processed/irrigation_anfis_dataset.csv`.
6. Compiles a 17-point validation report in `dataset_validation_report.md`.
7. Exports a chronological 70% / 15% / 15% time-series split specification in `dataset_split_info.json`.
