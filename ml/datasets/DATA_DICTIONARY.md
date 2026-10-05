# IrrigaSense Machine Learning Data Dictionary

## 1. Overview
This data dictionary documents the raw and processed irrigation datasets used in **IrrigaSense** for predictive soil moisture modeling and adaptive irrigation scheduling.

The dataset captures environmental, soil, irrigation, and future soil moisture dynamics collected from an experimental agricultural facility equipped with IoT sensor arrays and automated irrigation systems.

---

## 2. Experimental Sectors and Official Crop Mappings

| Zone ID | Sector / Crop Description | Cultivation System | Observation Start | Observation End | Total Raw Records |
|:-------:|:--------------------------|:-------------------|:------------------|:----------------|:------------------|
| **1**   | Tomato, open field        | Open Field         | 2025-02-28 15:00  | 2025-09-04 18:50| 9,531             |
| **2**   | Tomato, open field        | Open Field         | 2025-02-28 14:20  | 2025-09-23 10:10| 11,929            |
| **3**   | Tomato, pots              | Pots / Container   | 2025-02-14 13:10  | 2025-06-25 08:10| 1,118             |
| **4**   | Zucchini                  | Open Field         | 2025-03-01 07:10  | 2025-09-23 14:40| 12,676            |
| **5**   | Blueberry                 | Orchard / Bush     | 2025-02-11 09:20  | 2025-09-22 20:00| 11,814            |

*Sampling Interval:* Uniformly processed onto a **10-minute** time grid.

---

## 3. Column Descriptions & Specifications

### 3.1 Identifiers & Temporal Features
| Column Name | Type | Unit | Description | Input / Target Status |
|:------------|:-----|:-----|:------------|:----------------------|
| `zone` | Integer | 1–5 | Experimental zone identifier. | Input Feature |
| `crop` | String | Categorical | Official crop label derived from zone mapping. | Input Feature |
| `ts` | Timestamp | `YYYY-MM-DD HH:MM:SS` | Timestamp on 10-minute grid. Preserved for time-series ordering. | Time Metadata |
| `hour` | Integer | 0–23 | Hour of day (diurnal cycle proxy). | Input Feature |
| `month` | Integer | 1–12 | Calendar month (available in raw, excluded from ANFIS inputs). | Analysis Only |
| `day` | Integer | 1–31 | Day of month (available in raw, excluded from ANFIS inputs). | Analysis Only |
| `day_period` | Integer | 0–3 | Time-of-day category (available in raw, excluded from ANFIS inputs).| Analysis Only |
| `quarter` | Integer | 1–4 | Fiscal/seasonal quarter (available in raw, excluded from ANFIS inputs).| Analysis Only |

### 3.2 Meteorological Features
| Column Name | Type | Unit | Description | Input / Target Status |
|:------------|:-----|:-----|:------------|:----------------------|
| `weather_temp` | Float | °C | Ambient air temperature from on-site weather station. | Input Feature |
| `weather_humidity` | Float | % | Relative humidity (0–100%). | Input Feature |
| `weather_rain` | Float | mm | Precipitation accumulated over the 10-minute step. | Input Feature |
| `weather_pressure` | Float | hPa | Atmospheric barometric pressure. | Input Feature |
| `weather_wind_speed`| Float | km/h | Ambient wind speed. | Input Feature |
| `weather_radiation` | Float | W/m² | Solar radiation (pyranometer reading). | Input Feature |

### 3.3 Soil & Root-Zone Features
| Column Name | Type | Unit | Valid Range / Cleaning Rule | Description |
|:------------|:-----|:-----|:----------------------------|:------------|
| `soil_temperature_0-7cm` | Float | °C | Physical soil range | Soil temperature at shallow depth (0–7 cm). |
| `soil_temperature_7-18cm`| Float | °C | Physical soil range | Soil temperature at root depth (7–18 cm). |
| `ec` | Float | µS/cm | **0 to 1000** | Electrical conductivity. Sensor error codes (e.g., -32256, 31488) are filtered out. |
| `ph` | Float | pH scale | **3.0 to 9.0** | Soil/solution pH. Sensor error spikes (>9 or <3) are filtered out. |
| `soil_moisture` | Float | % Vol | 0–100% | Volumetric soil moisture content measured at current timestamp. Cleaned in preprocessed files. |

### 3.4 Irrigation & Operational Features
| Column Name | Type | Unit | Description | Input / Target Status |
|:------------|:-----|:-----|:------------|:----------------------|
| `irrigation_duration_minutes` | Float | Minutes | Duration of irrigation run during the current interval. | Input Feature |
| `water_vol_past_4h` | Float | Liters | Water applied over the preceding 4 hours (preceding 24 steps). | Input Feature |

---

## 4. Target Variables & Forward-Looking Leakage Prevention

| Variable Name | Type | Horizon | Definition | Input / Target Status |
|:--------------|:-----|:--------|:-----------|:----------------------|
| **`target_mean_24h`** | Float | +24 hours (+144 steps) | Mean volumetric soil moisture over the next 144 steps (24 hours). | **Primary Modeling Target ($y$)** |
| `target_point_24h` | Float | +24 hours (+144 steps) | Soil moisture instantaneous point 144 steps ahead. | **PROHIBITED AS INPUT** |
| `water_vol_to_24h` | Float | +24 hours (+144 steps) | Future water applied over next 144 steps. | **PROHIBITED AS INPUT** |
| `real_moisture_delta` | Float | +24 hours | Future soil moisture minus current soil moisture. | **PROHIBITED AS INPUT** |

> **CRITICAL DATA INTEGRITY RULE:**  
> Neither `target_point_24h`, `water_vol_to_24h`, nor `real_moisture_delta` may ever be used as predictive model inputs. `target_mean_24h` is the sole supervised learning target for Milestone 7 and is excluded from the input feature matrix $X$.
