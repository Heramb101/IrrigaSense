# IrrigaSense ANFIS Training Dataset — Validation & Audit Report

> **Milestone 7A Certification**  
> **Generated Date / Time:** 2026-10-06 03:42:33  
> **Total Processed Records:** 47,007 (from 47,068 raw sensor rows)  
> **Integrity Status:** PASSED (Zero leakage, zero missing values, validated physical bounds)

---

## 1. Zone Row Counts (Original vs. Cleaned)

| Zone ID | Official Crop Label | Original Rows | Cleaned Rows | Rows Removed | % Retained |
|:-------:|:--------------------|:--------------|:-------------|:-------------|:-----------|
| **Zone 1** | Tomato, open field | 9,531 | 9,531 | 0 | 100.00% |
| **Zone 2** | Tomato, open field | 11,929 | 11,929 | 0 | 100.00% |
| **Zone 3** | Tomato, pots | 1,118 | 1,090 | 28 | 97.50% |
| **Zone 4** | Zucchini | 12,676 | 12,676 | 0 | 100.00% |
| **Zone 5** | Blueberry | 11,814 | 11,781 | 33 | 99.72% |
| **Total** | *All Sectors* | **47,068** | **47,007** | **61** | **99.87%** |

---

## 2. Cleaning & Sensor Anomaly Audit

- **Rows removed due to invalid EC (< 0 or > 1000 µS/cm):** 45 records
  - Zone 3: 19 records (sensor error codes such as -32256, 31488)
  - Zone 5: 26 records (sensor error codes such as -32256, 31488)
- **Rows removed due to invalid pH (< 3 or > 9):** 45 records
  - Zone 3: 12 records
  - Zone 5: 33 records
- **Rows removed due to missing target (`target_mean_24h`):** 0 records
- **Rows removed due to missing input features:** 0 records
- **Total unique rows eliminated:** 61 records (0.13% of raw dataset)
- **Duplicate rows detected in final dataset:** 0

---

## 3. Missing Value Audit (Final Dataset)

| Variable | Role | Missing Count | % Missing | Status |
|:---------|:-----|:--------------|:----------|:-------|
| `zone` | Feature (X) | 0 | 0.00% | Verified Complete |
| `crop` | Feature (X) | 0 | 0.00% | Verified Complete |
| `ts` | Metadata | 0 | 0.00% | Verified Complete |
| `weather_temp` | Feature (X) | 0 | 0.00% | Verified Complete |
| `weather_humidity` | Feature (X) | 0 | 0.00% | Verified Complete |
| `weather_rain` | Feature (X) | 0 | 0.00% | Verified Complete |
| `weather_pressure` | Feature (X) | 0 | 0.00% | Verified Complete |
| `weather_wind_speed` | Feature (X) | 0 | 0.00% | Verified Complete |
| `weather_radiation` | Feature (X) | 0 | 0.00% | Verified Complete |
| `soil_temperature_0-7cm` | Feature (X) | 0 | 0.00% | Verified Complete |
| `soil_temperature_7-18cm` | Feature (X) | 0 | 0.00% | Verified Complete |
| `ec` | Feature (X) | 0 | 0.00% | Verified Complete |
| `ph` | Feature (X) | 0 | 0.00% | Verified Complete |
| `soil_moisture` | Feature (X) | 0 | 0.00% | Verified Complete |
| `irrigation_duration_minutes` | Feature (X) | 0 | 0.00% | Verified Complete |
| `water_vol_past_4h` | Feature (X) | 0 | 0.00% | Verified Complete |
| `hour` | Feature (X) | 0 | 0.00% | Verified Complete |
| `target_mean_24h` | Target (y) | 0 | 0.00% | Verified Complete |

---

## 4. Numeric Feature & Target Statistical Summary

| Feature Name | Minimum | Maximum | Mean | Median |
|:-------------|:--------|:--------|:-----|:-------|
| `weather_temp` |       1.7642 |      41.2850 |      24.8591 |      25.0283 |
| `weather_humidity` |      12.0000 |     100.0000 |      59.7586 |      59.0333 |
| `weather_rain` |       0.0000 |      19.5325 |       0.0406 |       0.0000 |
| `weather_pressure` |     996.1092 |    1029.4908 |    1010.5838 |    1010.6275 |
| `weather_wind_speed` |       0.0225 |      41.8175 |      11.8636 |      11.3250 |
| `weather_radiation` |       0.0000 |     813.3250 |     233.4564 |     112.7417 |
| `soil_temperature_0-7cm` |       4.3275 |      44.1817 |      27.1083 |      27.0550 |
| `soil_temperature_7-18cm` |       7.8000 |      33.3000 |      25.9714 |      27.5592 |
| `ec` |       0.0000 |     956.3333 |     198.6883 |     200.2500 |
| `ph` |       3.0000 |       8.2000 |       6.0037 |       6.0000 |
| `soil_moisture` |       0.0000 |     100.0000 |      49.1231 |      55.0000 |
| `irrigation_duration_minutes` |       0.0000 |      10.0000 |       0.4307 |       0.0000 |
| `water_vol_past_4h` |       0.0000 |     262.9000 |      11.3694 |       0.0000 |
| `hour` |       0.0000 |      23.0000 |      11.5804 |      12.0000 |
| `target_mean_24h` |       0.0000 |      95.8108 |      48.8686 |      53.7578 |

---

## 5. Crop & Zone Representation Breakdown

### Crop Distribution
| Crop Label | Record Count | Representation % |
|:-----------|:-------------|:-----------------|
| **Tomato, open field** | 21,460 | 45.65% |
| **Zucchini** | 12,676 | 26.97% |
| **Blueberry** | 11,781 | 25.06% |
| **Tomato, pots** | 1,090 | 2.32% |

### Zone Distribution
| Zone ID | Record Count | Representation % |
|:--------|:-------------|:-----------------|
| **Zone 1** | 9,531 | 20.28% |
| **Zone 2** | 11,929 | 25.38% |
| **Zone 3** | 1,090 | 2.32% |
| **Zone 4** | 12,676 | 26.97% |
| **Zone 5** | 11,781 | 25.06% |

---

## 6. Time-Series Chronological Split Plan

- **Earliest Dataset Timestamp:** `2025-02-14 23:50:00`
- **Latest Dataset Timestamp:** `2025-09-23 14:40:00`

| Partition | Ratio | Records | Start Timestamp | End Timestamp |
|:----------|:------|:--------|:----------------|:--------------|
| **Training** | 70% | 32,905 (70.0%) | `2025-02-14 23:50:00` | `2025-08-24 08:20:00` |
| **Validation** | 15% | 7,051 (15.0%) | `2025-08-24 08:20:00` | `2025-09-06 13:30:00` |
| **Testing** | 15% | 7,051 (15.0%) | `2025-09-06 13:30:00` | `2025-09-23 14:40:00` |
| **Total** | 100% | **47,007** | `2025-02-14 23:50:00` | `2025-09-23 14:40:00` |

---

## 7. Data Integrity & Leakage Verification (Items 15–17)

- [x] **Item 15 — Forward-Looking Leakage Check:** None of the forward-looking target columns (`target_point_24h`, `water_vol_to_24h`, `real_moisture_delta`) are present in the final modeling feature list or exported CSV. (Detected leakage columns: `[]`)
- [x] **Item 16 — Target Isolation Check:** `target_mean_24h` is cleanly isolated as the supervised regression target ($y$). It is **NOT** present in the input feature matrix ($X$).
- [x] **Item 17 — Prohibited Model Inputs Check:** `target_point_24h`, `water_vol_to_24h`, and `real_moisture_delta` are strictly excluded from predictive model inputs.

---

## 8. Summary Conclusion

The prepared dataset `irrigation_anfis_dataset.csv` is fully cleaned, physically bounded, chronologically sorted, and rigorously verified against target leakage. It is certified ready for ANFIS membership function design and rule-base training in subsequent milestones.
