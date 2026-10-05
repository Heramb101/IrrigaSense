# IrrigaSense — Open-Meteo Soil Moisture Feasibility POC Report

> **Milestone 7D Technical Specification & Verification Report**  
> **Investigation Component:** Part A — Automated Soil Moisture Retrieval Feasibility  
> **Script Prototype:** `ml/datasets/open_meteo_soil_moisture_poc.py`  
> **Machine-Readable Probe Artifact:** `ml/datasets/processed/open_meteo_soil_moisture_probe.json`  
> **Reference Test Location:** Baramati North Farmland, Pune District, Maharashtra ($18.1550^\circ\text{N}, 74.5800^\circ\text{E}$)  
> **HTTP Status:** 200 OK (Verified Live API Call)

---

## 1. Executive Summary

Milestone 7C revealed that while volumetric soil moisture (`soil_moisture`) is the single strongest empirical predictor of future moisture in the Mendeley dataset ($r = 0.9640$, $\Delta R^2 = 1.6113$), the live IrrigaSense application has no physical IoT sensor probe installed on farmers' fields. Furthermore, strictly adhering to the **minimal farmer input rule** prohibits asking farmers to estimate soil moisture.

This proof-of-concept (POC) investigated whether the official **Open-Meteo Forecast API** can serve as an automated, zero-hardware, zero-farmer-input source of soil moisture and secondary environmental drivers (`shortwave_radiation`, `surface_pressure`).

### Core Finding:
**Open-Meteo fully supports real-time and forecast volumetric soil moisture across four distinct agricultural depth layers with zero missing values and standard SI units ($m^3/m^3$).** 
This confirms that Strategy B (automated soil moisture ingestion) is technically viable for production without adding a single question to the farmer workflow.

---

## 2. API Endpoint & Query Specification

- **Official Endpoint:** `https://api.open-meteo.com/v1/forecast`
- **Authentication:** None required (Public / Open-Access tier).
- **Transport Protocol:** HTTPS GET with JSON response payload.
- **Configurable Coordinate Mechanism:** CLI arguments (`--latitude`, `--longitude`) and environment variables (`OPEN_METEO_LATITUDE`, `OPEN_METEO_LONGITUDE`).
- **Query Parameter Structure:**
  ```text
  https://api.open-meteo.com/v1/forecast?latitude=18.1550&longitude=74.5800&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,surface_pressure,shortwave_radiation,soil_moisture_0_to_7cm,soil_moisture_7_to_28cm,soil_moisture_28_to_100cm,soil_moisture_100_to_255cm&hourly=soil_moisture_0_to_7cm,soil_moisture_7_to_28cm,soil_moisture_28_to_100cm,soil_moisture_100_to_255cm,surface_pressure,shortwave_radiation&daily=et0_fao_evapotranspiration,shortwave_radiation_sum&timezone=auto&forecast_days=3
  ```

---

## 3. Verified Soil Moisture Variables & Agricultural Layers

The Open-Meteo API was tested across four standard depth intervals corresponding to the ECMWF Integrated Forecasting System (IFS) land surface model (HTESSEL):

| API Parameter Name | Depth Layer | Agricultural / Agronomic Role | Live Probe Value | Converted VWC % | Supported in `current`? | Supported in `hourly`? |
|:---|:---:|:---|:---:|:---:|:---:|:---:|
| **`soil_moisture_0_to_7cm`** | **0–7 cm** | **Surface / Seedbed Layer:** Governs seed emergence, direct soil evaporation, and initial infiltration. | $0.297\text{ m}^3/\text{m}^3$ | **29.70%** | **YES** | **YES** |
| **`soil_moisture_7_to_28cm`** | **7–28 cm** | **Active Root Zone (Vegetables):** Primary extraction depth for shallow-to-medium rooted crops (tomatoes, onions, zucchini, pulses). | $0.265\text{ m}^3/\text{m}^3$ | **26.50%** | **YES** | **YES** |
| **`soil_moisture_28_to_100cm`**| **28–100 cm**| **Deep Root Zone (Orchards / Cane):** Active extraction zone for perennial fruits, sugarcane, and mature cotton taproots. | $0.303\text{ m}^3/\text{m}^3$ | **30.30%** | **YES** | **YES** |
| **`soil_moisture_100_to_255cm`**| **100–255 cm**| **Vadose Subsoil Reservoir:** Deep hydrological recharge and capillary rise reserve. | $0.382\text{ m}^3/\text{m}^3$ | **38.20%** | **YES** | **YES** |

### Unit Standardization:
- **API Unit:** Cubic meters of water per cubic meter of bulk soil ($\text{m}^3/\text{m}^3$).
- **Conversion to Percentage:** 
  $$\text{Volumetric Water Content (\% VWC)} = \text{Value}_{\text{raw}} \times 100.0$$
  This directly maps Open-Meteo outputs into the same physical percentage scale ($0$–$100\%$) utilized by the Mendeley dataset and IrrigaSense ANFIS feature pipeline.

---

## 4. Secondary Variables Verification (Radiation & Pressure)

In Milestone 7C, solar radiation (`weather_radiation`) and barometric pressure (`weather_pressure`) were audited as candidate features in Set B. The POC verified their availability in the Open-Meteo Forecast API:

| Variable Name | API Key | Layer / Interval | Live Value | Units | Alignment with Dataset |
|:---|:---|:---|:---:|:---:|:---|
| **Shortwave Solar Radiation** | `shortwave_radiation` | Current (15-min interval) & Hourly | $0.0$ (night) to $867.0$ (noon) | $\text{W/m}^2$ | **Exact Match:** Mendeley dataset `weather_radiation` is in $\text{W/m}^2$. |
| **Daily Solar Radiation Sum** | `shortwave_radiation_sum` | Daily Aggregation | $20.84$ | $\text{MJ/m}^2$ | Excellent for daily Penman-Monteith energy balance. |
| **Surface Atmospheric Pressure** | `surface_pressure` | Current & Hourly | $952.2$ | $\text{hPa}$ | **Exact Match:** Mendeley dataset `weather_pressure` is in $\text{hPa}$. |
| **Reference Evapotranspiration** | `et0_fao_evapotranspiration`| Daily Aggregation | $4.73$ | $\text{mm}$ | Production asset already utilized in IrrigaSense. |

---

## 5. Temporal Resolution, Horizon, and Data Quality

- **Current Retrieval Interval:** Open-Meteo updates current variables on a **15-minute rolling window** (`interval: 900 seconds`).
- **Hourly Forecast Horizon:** The API returns up to 72 hours (3 days) or 168 hours (7 days) of forward-looking predictions.
- **Null / Missing Value Audit:** Across 72 consecutive hourly steps for all six tested parameters:
  - `soil_moisture_0_to_7cm`: **0 nulls / 72 steps** (Min: 0.265, Max: 0.312)
  - `soil_moisture_7_to_28cm`: **0 nulls / 72 steps** (Min: 0.259, Max: 0.265)
  - `soil_moisture_28_to_100cm`: **0 nulls / 72 steps** (Min: 0.299, Max: 0.303)
  - `soil_moisture_100_to_255cm`: **0 nulls / 72 steps** (Min: 0.382, Max: 0.383)
  - `surface_pressure`: **0 nulls / 72 steps** (Min: 950.6 hPa, Max: 957.1 hPa)
  - `shortwave_radiation`: **0 nulls / 72 steps** (Min: 0.0 W/m², Max: 867.0 W/m²)
- **Missing Value Conclusion:** **Zero missing or null values.** The Open-Meteo numerical weather prediction and land-surface data pipeline is fully continuous.

---

## 6. Practical Production Suitability for IrrigaSense

| Architectural Criteria | Evaluation | Operational Verdict |
|:---|:---|:---|
| **Farmer Burden** | **Zero.** Retrieved using coordinates from Question 1 (Google Maps). | **PASS** — Adheres strictly to the 6-question workflow constraint. |
| **Hardware Dependency** | **Zero.** Cloud-to-cloud API call; no in-ground sensors or gateways. | **PASS** — Eliminates farmer capital expenditure (\$0.00 cost). |
| **API Latency** | **Fast.** The probe call completed in **~380 ms** over public HTTPS. | **PASS** — Can be queried seamlessly during assessment submission. |
| **Root-Zone Match** | **High.** `soil_moisture_7_to_28cm` matches the 7–18 cm root zone studied in 7B. | **PASS** — Provides multi-tier vertical profile. |
| **Codebase Impact** | **Isolated.** Tested without touching `app/services/environment/open_meteo.py`. | **PASS** — Safe prototype path. |

---

## 7. Critical Technical Caveats & Limitations

While Open-Meteo soil moisture availability is an outstanding engineering asset, the following fundamental agronomic differences must be explicitly understood:

1. **Model-Derived Estimate vs. In-Situ Sensor Ground Truth:**
   - **Mendeley Dataset Soil Moisture:** Derived from physical, in-situ Campbell Scientific TDR sensors embedded directly in the root zone of specific experimental plots.
   - **Open-Meteo Soil Moisture:** Derived from global numerical weather prediction land surface models (ECMWF H-TESSEL / ERA5-Land). It simulates water transport through soil layers using atmospheric water flux and pedotransfer estimates.
   - **Implication:** Open-Meteo provides an *environmental estimate* of soil wetness on a ~9 km to 25 km grid cell. It does not measure instantaneous localized valve pulses or micro-topography within an individual furrow.
2. **Predictive Transfer Caution:**
   - As emphasized in Milestone 7C, **we cannot assume that because sensor-measured soil moisture is 96.4% predictive, Open-Meteo model-derived soil moisture will exhibit identical fidelity.**
   - In Part B of this milestone, we conduct a controlled feature ablation to establish the empirical baseline difference between models with and without soil moisture.

---

## 8. Final Recommendation for Part A

- **API Feasibility Status:** **PASS** (Available and verified).
- **Recommended Next Step for Production Pipeline:**
  In a future milestone (Milestone 7E / Production Integration), expand `backend/app/services/environment/open_meteo.py` to add `soil_moisture_0_to_7cm`, `soil_moisture_7_to_28cm`, and `shortwave_radiation` to the existing `WeatherProfile` response schema.
- **Current Action:** Maintain isolated status. Proceed directly to **Part B (Controlled Feature Ablation)** to quantify the predictive contribution of soil moisture.
