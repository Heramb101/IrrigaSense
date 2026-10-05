# IrrigaSense — Feature Analysis and ANFIS Input Selection Report

> **Milestone 7B Technical Specification**  
> **Generated Date / Time:** 2026-10-06 03:42:59  
> **Master Dataset:** `ml/datasets/processed/irrigation_anfis_dataset.csv` (47,007 rows, certified unmodified)  
> **Methodology:** Leakage-safe chronological validation (Train 70% / Val 15% / Test 15% untouched)  
> **Recommended ANFIS Input Architecture:** **Set B (8 features)** with **Set C (5 features)** as compact alternative

---

## 1. Dataset Summary

- **Total Cleaned Records:** `47,007` rows across 5 experimental sectors on a 10-minute time grid.
- **Chronological Train Partition:** `32,905` rows (`2025-02-14 23:50:00` to `2025-08-24 08:20:00`). All feature selection, correlation calculations, mutual information, and model fittings were strictly constrained to this partition.
- **Chronological Validation Partition:** `7,051` rows (`2025-08-24 08:20:00` to `2025-09-06 13:30:00`). Used exclusively for feature set comparison and permutation importance.
- **Chronological Test Partition:** `7,051` rows (`2025-09-06 13:30:00` to `2025-09-23 14:40:00`). **100% UNTOUCHED** (reserved for future Milestone 7 ANFIS evaluation).
- **Data Quality:** Zero missing values, zero duplicated rows, physical bounds validated (`0 <= ec <= 1000`, `3.0 <= ph <= 9.0`).

---

## 2. Candidate Features Evaluated

A total of 14 continuous numerical features present in the master dataset were evaluated as candidate inputs:
1. `weather_temp` (Ambient air temperature, °C)
2. `weather_humidity` (Relative humidity, %)
3. `weather_rain` (10-minute precipitation, mm)
4. `weather_pressure` (Atmospheric barometric pressure, hPa)
5. `weather_wind_speed` (Ambient wind speed, km/h)
6. `weather_radiation` (Solar radiation, W/m²)
7. `soil_temperature_0-7cm` (Shallow soil temperature, °C)
8. `soil_temperature_7-18cm` (Root-zone soil temperature, °C)
9. `ec` (Electrical conductivity, µS/cm)
10. `ph` (Soil pH scale)
11. `soil_moisture` (Current volumetric soil moisture, %)
12. `irrigation_duration_minutes` (Current irrigation interval valve duration, min)
13. `water_vol_past_4h` (Preceding 4-hour cumulative water applied, L)
14. `hour` (Hour of day: 0–23)

---

## 3. Features Excluded and Rationale

| Variable | Category | Exclusion Reason |
|:---------|:---------|:-----------------|
| `target_point_24h` | Target Leakage | Forward-looking instantaneous soil moisture 24h ahead. Strictly forbidden. |
| `water_vol_to_24h` | Target Leakage | Forward-looking cumulative irrigation applied over the next 24h. Strictly forbidden. |
| `real_moisture_delta`| Target Leakage | Future soil moisture delta ($\Delta \theta_{24h}$). Strictly forbidden. |
| `target_mean_24h` | Target (y) | Primary supervised target. Excluded from input matrix $X$. |
| `zone` | Identifier | Categorical sector ID (1–5). Arbitrary integer mapping introduces false ordinal bias into fuzzy membership functions. |
| `crop` | Categorical | Categorical crop label. Kept for stratified evaluation; not encoded into first continuous ANFIS model. |
| `irrigation_duration_minutes` | Deployment Mismatch | **Crucial Deployment Finding:** Represents concurrent valve-opening duration during the sampled 10-minute step. At deployment time, IrrigaSense issues an advisory **prior** to irrigating, meaning valve duration is unknown/zero when the recommendation is requested. Furthermore, validation permutation importance was negative ($-0.000009$), confirming zero incremental predictive utility. |
| `soil_temperature_0-7cm` | Redundancy | Collinear with `weather_temp` ($r = 0.9585$). Requires in-ground physical hardware, whereas `weather_temp` is readily accessible from live weather APIs. |
| `soil_temperature_7-18cm` | Generalization Drag | Displayed negative validation permutation importance ($-0.0040$), indicating chronological domain overfitting. |

---

## 4. Correlation Findings (Training Partition)

Correlations evaluated against `target_mean_24h` on the training set (32,905 rows):

| Rank | Feature | Pearson Correlation ($r$) | Spearman Correlation ($ho$) | Absolute Spearman ($|\rho|$) | Physical Role |
|:----:|:--------|:--------------------------|:------------------------------|:-----------------------------|:--------------|
| 1 | `soil_moisture` | +0.9640 | +0.9512 | 0.9512 | Strong baseline state |
| 2 | `ec` | +0.5916 | +0.5175 | 0.5175 | Salinity/Soil proxy |
| 3 | `water_vol_past_4h` | +0.1979 | +0.3010 | 0.3010 | Environmental/Operational |
| 4 | `soil_temperature_7-18cm` | -0.2611 | -0.1762 | 0.1762 | Environmental/Operational |
| 5 | `irrigation_duration_minutes` | +0.1184 | +0.1321 | 0.1321 | Environmental/Operational |
| 6 | `weather_radiation` | +0.0798 | +0.1118 | 0.1118 | Environmental/Operational |
| 7 | `weather_pressure` | +0.1121 | +0.1013 | 0.1013 | Environmental/Operational |
| 8 | `soil_temperature_0-7cm` | -0.1586 | -0.1009 | 0.1009 | Environmental/Operational |
| 9 | `weather_temp` | -0.1585 | -0.0979 | 0.0979 | Environmental/Operational |
| 10 | `weather_wind_speed` | +0.0678 | +0.0620 | 0.0620 | Environmental/Operational |
| 11 | `weather_humidity` | -0.0201 | -0.0447 | 0.0447 | Environmental/Operational |
| 12 | `ph` | -0.0117 | +0.0431 | 0.0431 | Environmental/Operational |
| 13 | `weather_rain` | +0.0372 | +0.0164 | 0.0164 | Environmental/Operational |
| 14 | `hour` | +0.0069 | +0.0017 | 0.0017 | Environmental/Operational |

> **Key Insight:** `soil_moisture` exhibits the dominant rank correlation ($\rho = 0.9512$), reflecting that future 24h mean moisture is anchored to antecedent moisture. `ec` ($\rho = 0.5175$) and `water_vol_past_4h` ($\rho = 0.3010$) provide the next highest independent explanatory capacity.

---

## 5. Feature Redundancy Findings (|r| >= 0.85)

| Feature 1 | Feature 2 | Pearson $r$ | Diagnostic & Architectural Decision |
|:----------|:----------|:------------|:------------------------------------|
| `weather_temp` | `soil_temperature_0-7cm` | **+0.9585** | **Direct Redundancy:** Shallow soil temperature tracks air temperature almost 1-to-1 throughout the diurnal solar cycle. `soil_temperature_0-7cm` was pruned in favor of `weather_temp`, which is automatically obtainable via Open-Meteo without specialized farmer probe hardware. |

---

## 6. Non-ANFIS Baseline Model Results

To establish an empirical predictive ceiling, a `RandomForestRegressor` (100 estimators, max depth 12) was trained strictly on the training partition and evaluated on the chronological validation partition:

- **Validation MAE:** `3.8645%` volumetric soil moisture
- **Validation RMSE:** `8.5958%`
- **Validation $R^2$:** `0.8895` (88.95% variance explained across chronological unseen boundary)

---

## 7. Feature Importance Audit

Permutation importance on the validation set measures the true degradation in model $R^2$ when each feature's chronological integrity is scrambled:

| Rank | Feature | Permutation Importance Mean ($\Delta R^2$) | Permutation Std | Native Tree Gini Importance |
|:----:|:--------|:--------------------------------------------|:----------------|:----------------------------|
| 1 | `soil_moisture` | +1.611301 | ±0.014457 | 0.9359 |
| 2 | `ec` | +0.164304 | ±0.003241 | 0.0154 |
| 3 | `ph` | +0.011103 | ±0.000856 | 0.0202 |
| 4 | `weather_wind_speed` | +0.001305 | ±0.000271 | 0.0015 |
| 5 | `weather_radiation` | +0.001223 | ±0.000080 | 0.0013 |
| 6 | `weather_pressure` | +0.000912 | ±0.000131 | 0.0026 |
| 7 | `water_vol_past_4h` | +0.000366 | ±0.000095 | 0.0041 |
| 8 | `hour` | +0.000334 | ±0.000244 | 0.0011 |
| 9 | `weather_humidity` | +0.000146 | ±0.000096 | 0.0009 |
| 10 | `soil_temperature_0-7cm` | +0.000085 | ±0.000109 | 0.0010 |
| 11 | `weather_temp` | +0.000065 | ±0.000141 | 0.0026 |
| 12 | `irrigation_duration_minutes` | -0.000009 | ±0.000008 | 0.0001 |
| 13 | `weather_rain` | -0.000027 | ±0.000010 | 0.0001 |
| 14 | `soil_temperature_7-18cm` | -0.004008 | ±0.002792 | 0.0131 |

---

## 8. Mutual Information (Non-Linear Dependency)

Mutual information ($I(X; Y)$ in nats) captures non-linear, non-monotonic relationships on the training set:

| Rank | Feature | Mutual Information (nats) | Interpretation |
|:----:|:--------|:--------------------------|:---------------|
| 1 | `soil_moisture` | 1.8515 | Primary driver |
| 2 | `ec` | 1.7231 | Primary driver |
| 3 | `soil_temperature_7-18cm` | 1.4266 | Primary driver |
| 4 | `ph` | 1.3460 | Primary driver |
| 5 | `weather_pressure` | 1.1849 | Primary driver |
| 6 | `hour` | 0.6281 | Moderate dependency |
| 7 | `water_vol_past_4h` | 0.6082 | Moderate dependency |
| 8 | `weather_temp` | 0.6040 | Moderate dependency |
| 9 | `soil_temperature_0-7cm` | 0.5783 | Moderate dependency |
| 10 | `weather_humidity` | 0.4050 | Moderate dependency |
| 11 | `weather_wind_speed` | 0.3968 | Moderate dependency |
| 12 | `weather_radiation` | 0.2063 | Low dependency |
| 13 | `irrigation_duration_minutes` | 0.0619 | Low dependency |
| 14 | `weather_rain` | 0.0491 | Low dependency |

---

## 9. Zone & Crop Stratified Dynamics

Evaluating soil moisture and target distributions across experimental sectors:

| Zone ID | Crop Label | Records | Target Mean (Std) | Target Median | Current SM Mean (Median) | $r(\text{SM}, \text{Target})$ |
|:-------:|:-----------|:--------|:------------------|:--------------|:-------------------------|:-------------------------------|
| **Zone 1** | Tomato, open field | 9,531 | 32.22% (±14.60) | 22.72% | 32.44% (23.00%) | **+0.9200** |
| **Zone 2** | Tomato, open field | 11,929 | 25.32% (±13.14) | 18.64% | 25.51% (19.00%) | **+0.9524** |
| **Zone 3** | Tomato, pots | 1,090 | 77.53% (±10.78) | 74.54% | 77.25% (79.00%) | **+0.3632** |
| **Zone 4** | Zucchini | 12,676 | 76.51% (±10.55) | 79.25% | 76.73% (80.00%) | **+0.8972** |
| **Zone 5** | Blueberry | 11,781 | 53.79% (±27.06) | 66.25% | 54.23% (66.00%) | **+0.9779** |

> **Observation:** Open-field crops (Tomato Zone 1 & 2) operate in drier soil moisture regimes (mean 25–32%), while potted plants and zucchini maintain high moisture levels (76–77%). Within every single zone, antecedent soil moisture strongly correlates with 24h future moisture ($r \ge 0.89$, except container potted tomato where frequent pulse-irrigation creates high transient volatility).

---

## 10. Multi-Set Performance Comparison (Set A vs. Set B vs. Set C)

To test whether pruning features causes predictive degradation, three distinct feature sets were fitted on the training partition and evaluated on the chronological validation partition:

| Feature Set | Input Count | Features Included | Validation MAE | Validation RMSE | Validation $R^2$ |
|:------------|:-----------:|:------------------|:--------------:|:---------------:|:----------------:|
| **Set A (Broad — 13 Features)** | 13 | `weather_temp`, `weather_humidity`, `weather_rain`, `weather_pressure`, `weather_wind_speed`, `weather_radiation`, `soil_temperature_0-7cm`, `soil_temperature_7-18cm`, `ec`, `ph`, `soil_moisture`, `water_vol_past_4h`, `hour` | **3.8244%** | **8.5609%** | **0.8904** |
| **Set B (Reduced — 8 Features)** | 8 | `soil_moisture`, `ec`, `water_vol_past_4h`, `weather_temp`, `weather_radiation`, `weather_wind_speed`, `weather_humidity`, `weather_pressure` | **3.4545%** | **7.9426%** | **0.9057** |
| **Set C (Compact — 5 Features)** | 5 | `soil_moisture`, `ec`, `water_vol_past_4h`, `weather_temp`, `weather_radiation` | **3.3614%** | **7.8554%** | **0.9078** |

> **Crucial Empirical Finding:**  
> **Set B (8 features)** and **Set C (5 features)** both **outperform Set A (13 features)** on chronological validation! Set C achieves an $R^2$ of **0.9078** and MAE of **3.3614%** (compared to Set A's $R^2 = 0.8904$ and MAE of $3.8244%$). Pruning redundant, collinear, and noisy features actively improves out-of-sample temporal generalization by preventing tree over-parameterization.

---

## 11. Recommended ANFIS Input Architecture

For an Adaptive Neuro-Fuzzy Inference System, input dimensionality is constrained by rule explosion ($M^N$ rules for $M$ membership functions and $N$ inputs).

### Primary Recommendation: **Set B (8 Features)**
1. `soil_moisture` (Current soil volumetric moisture)
2. `ec` (Electrical conductivity / soil salinity & fertility proxy)
3. `water_vol_past_4h` (Cumulative water delivered over preceding 4 hours)
4. `weather_temp` (Ambient temperature)
5. `weather_radiation` (Solar radiation / primary energy for evapotranspiration)
6. `weather_wind_speed` (Aerodynamic boundary layer vapor conductance)
7. `weather_humidity` (Vapor pressure deficit driver)
8. `weather_pressure` (Atmospheric synoptic driver)

### High-Parsimony Alternative: **Set C (5 Features)**
For a lightweight, highly interpretable ANFIS with only $2^5 = 32$ fuzzy rules:
1. `soil_moisture`
2. `ec`
3. `water_vol_past_4h`
4. `weather_temp`
5. `weather_radiation`

---

## 12. Supervised Target Variable

- **Target:** `target_mean_24h`
- **Definition:** Mean volumetric soil moisture content over the upcoming 144 steps (24 hours).
- **Physical Units:** Percentage volumetric water content (%).
- **Modeling Role:** Continuous regression output.

---

## 13. Rationale for Each Selected Feature

| Feature | Physical Justification | Empirical Justification |
|:--------|:-----------------------|:-------------------------|
| `soil_moisture` | Direct physical state of the root zone reservoir. | Top ranked across Pearson ($0.9640$), Spearman ($0.9512$), MI ($1.8515$), and Permutation Importance ($1.6113$). |
| `ec` | Reflects dissolved ion concentration, soil solution matrix potential, and distinct sector baseline. | Rank 2 correlation ($0.5175$), MI ($1.7232$), Permutation Importance ($0.1643$). |
| `water_vol_past_4h` | Captures recent antecedent water application and infiltration wetting front. | Backward-looking operational driver; Spearman correlation ($0.3010$), MI ($0.6082$). |
| `weather_temp` | Primary thermodynamic variable driving sensible heat flux and plant transpiration. | Major driver of potential evapotranspiration ($ET_0$). |
| `weather_radiation` | Net radiative energy driving latent heat flux and crop water consumption. | Permutation importance positive; essential physical component of Penman-Monteith equation. |
| `weather_wind_speed` | Controls turbulent convective vapor transport away from canopy boundary layer. | Key Penman-Monteith aerodynamic term. |
| `weather_humidity` | Dictates atmospheric vapor pressure deficit (VPD). | Low relative humidity accelerates leaf transpiration and soil surface drying. |
| `weather_pressure` | Synoptic weather indicator (high pressure clear skies vs low pressure storm fronts). | Enhances atmospheric contextual stability in Set B. |

---

## 14. Live IrrigaSense Application Compatibility

| Selected Feature | Production Source in IrrigaSense | Availability Status | Farmer Burden |
|:-----------------|:---------------------------------|:--------------------|:--------------|
| `weather_temp` | **Open-Meteo Live API** | Live / Automated | **Zero** |
| `weather_humidity` | **Open-Meteo Live API** | Live / Automated | **Zero** |
| `weather_wind_speed`| **Open-Meteo Live API** | Live / Automated | **Zero** |
| `weather_radiation` | **Open-Meteo Live API** | Live / Automated | **Zero** |
| `weather_pressure` | **Open-Meteo Live API** | Live / Automated | **Zero** |
| `ec` | **SoilGrids REST API / Regional Database** | Live / Automated | **Zero** |
| `soil_moisture` | In-situ IoT Soil Moisture Probe / Sat Soil Moisture API | Automated / Sensor feed | **Zero** |
| `water_vol_past_4h` | Smart Irrigation Valve Flowmeter Log | Automated / Sensor log | **Zero** |

> **Deployment Compliance:** All selected features can be gathered automatically via Open-Meteo weather APIs, SoilGrids edaphic endpoints, and IoT valve/moisture telemetry without placing additional input burden on the farmer workflow.

---

## 15. Limitations & Future Modeling Considerations

1. **Container vs. Field Dynamics:** Zone 3 (potted tomatoes) exhibited lower correlation between current and future soil moisture ($r = 0.36$) due to restricted root volume and frequent pulse-fertigation. In contrast, all open-field and orchard zones exhibited $r \ge 0.89$.
2. **Zone 3 Temporal Truncation:** Zone 3 records concluded on `2025-06-25`, meaning potted container dynamics are solely present in the training partition. For field-scale deployment in IrrigaSense, open-field dynamics (Zones 1, 2, 4, 5) dominate.
3. **ANFIS Fuzzy Partitioning:** If standard grid partitioning is utilized for ANFIS, Set C (5 inputs $\rightarrow 2^5 = 32$ rules) will train significantly faster than Set B (8 inputs $\rightarrow 2^8 = 256$ rules). If Subtractive Clustering or Fuzzy C-Means (FCM) is adopted, Set B can be deployed with a compact set of cluster-derived rules ($10$–$25$ rules).
4. **No Claim of Global Optimality:** These candidate feature sets represent the recommended inputs derived from empirical and physical evaluation of this 47,007-record multi-zone dataset.
