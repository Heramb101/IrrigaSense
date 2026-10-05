# IrrigaSense — Production Feature Availability & Data Bridge Audit

> **Milestone 7C Technical Specification & Codebase Audit**  
> **Target Dataset:** `ml/datasets/processed/irrigation_anfis_dataset.csv` (47,007 rows)  
> **Milestone Reference:** `ml/datasets/processed/feature_selection_report.md` (Milestone 7B)  
> **System Architecture Status:** Live verification of Google Maps, Open-Meteo (`app/services/environment/open_meteo.py`), and SoilGrids (`app/services/environment/soilgrids.py`) integrations.  
> **Core UX Constraint:** Strict preservation of the minimal six-question farmer workflow. Zero new questions permitted.

---

## 1. Executive Summary & Purpose

In Milestone 7B, feature analysis demonstrated that future 24-hour mean soil moisture (`target_mean_24h`) can be predicted with high precision ($R^2 \approx 0.908$, MAE $\approx 3.36\%$) using parsimonious input subsets (Set B with 8 features or Set C with 5 features). However, Milestone 7B assumed that candidate features would be readily accessible at deployment time.

The objective of **Milestone 7C** is to execute an uncompromising, code-level audit of the actual IrrigaSense production system to determine how—and whether—the candidate features can be supplied at runtime. 

### Core Audit Principles:
1. **No Assumed Availability:** A feature is NOT available in production merely because it exists in the training dataset or because an external API could theoretically provide it. It must be implemented and operational in the IrrigaSense codebase.
2. **Minimal Farmer Input Guarantee:** IrrigaSense is architected to minimize cognitive burden on farmers. Under no circumstances may sensor-grade parameters (volumetric soil moisture, electrical conductivity, preceding liter volumes, solar radiation) be converted into farmer questions.
3. **No Unimplemented Claims:** The audit explicitly forbids claiming that SoilGrids provides live moisture or EC, that Open-Meteo provides valve history, or that IoT flowmeters are currently installed.

---

## 2. Inventory of Current IrrigaSense Production Data Sources

The active IrrigaSense production codebase was inspected across `backend/app/services/environment/`, `backend/app/schemas/`, and `frontend/src/assessment/`. Currently implemented data sources provide the following exact parameters:

### 2.1 Google Maps Geolocation Integration
- **Source:** Google Maps JavaScript API Loader & Geocoding Service (`frontend/src/components/questions/LocationQuestion.tsx`).
- **Available Fields:**
  - `latitude` (float, decimal degrees WGS84)
  - `longitude` (float, decimal degrees WGS84)
  - `place_name` (string, reverse-geocoded descriptive administrative location)
- **Status:** Fully implemented, verified with fallback geocoding.

### 2.2 Open-Meteo Weather Service
- **Source:** REST client calling `https://api.open-meteo.com/v1/forecast` (`backend/app/services/environment/open_meteo.py`).
- **Active Query Parameters:**
  - `current`: `temperature_2m`, `relative_humidity_2m`, `precipitation`, `wind_speed_10m`
  - `daily`: `et0_fao_evapotranspiration`
  - `timezone`: `auto`
- **Normalized Internal Output (`WeatherProfile`):**
  - `temperature_c` (Current 2m air temperature, °C)
  - `humidity_percent` (Current relative humidity, %)
  - `precipitation_mm` (Current precipitation rate, mm)
  - `wind_speed_kmh` (Current 10m wind speed, km/h)
  - `et0_mm` (Daily FAO-56 Reference Evapotranspiration, mm)
- **Status:** Fully implemented with strict timeout, HTTP status, and validation error handling.

### 2.3 ISRIC SoilGrids 1.0.0 Web Coverage Service (WCS)
- **Source:** OWSLib WebCoverageService querying ISRIC GeoTIFF coverages (`backend/app/services/environment/soilgrids.py`).
- **Active Coverages (0–5cm depth layer):**
  - `phh2o_0-5cm_mean`: Soil pH in $H_2O$ (scaled by 0.1)
  - `nitrogen_0-5cm_mean`: Total nitrogen in g/kg (scaled by 0.01)
  - `soc_0-5cm_mean`: Soil organic carbon in g/kg (scaled by 0.1)
  - `sand_0-5cm_mean`: Sand mass fraction % (scaled by 0.1)
  - `silt_0-5cm_mean`: Silt mass fraction % (scaled by 0.1)
  - `clay_0-5cm_mean`: Clay mass fraction % (scaled by 0.1)
  - `bdod_0-5cm_mean`: Bulk density of fine earth fraction in g/cm³ (scaled by 0.01)
- **Normalized Internal Output (`SoilProfile`):**
  - `ph`, `nitrogen`, `organic_carbon`, `sand_percent`, `silt_percent`, `clay_percent`, `bulk_density`.
- **Status:** Fully implemented with Homolosine projection transformation (`pyproj`), multi-threaded raster fetches, and robust fallback handling.

### 2.4 Six-Question Farmer Assessment Workflow
- **Source:** Farmer onboarding wizard (`frontend/src/assessment/assessmentConfig.ts`).
- **Active Questions:**
  - **Q1 (Location):** Latitude, longitude, place name (Google Maps marker confirmation).
  - **Q2 (Crop):** Selected crop identifier (e.g., Tomato, Sugarcane, Cotton, Wheat, Onion).
  - **Q3 (Planting Date):** Sowing or transplanting date (derives crop cycle stage).
  - **Q4 (Farm Size):** Cultivated plot acreage (categorical range or exact decimal).
  - **Q5 (Irrigation Method):** Application infrastructure (Drip, Sprinkler, Furrow, Flood).
  - **Q6 (Water Availability):** Supply constraint (Continuous 24/7, Restricted 4–8h, Canal rotation, Highly intermittent).
- **Status:** Fully implemented, verified by 12 end-to-end frontend flow tests.

---

## 3. Comprehensive Feature Availability & Audit Table

Every feature analyzed in Milestone 7B, along with operational parameters from Open-Meteo and SoilGrids, is audited below against the live IrrigaSense production codebase.

| Feature Name | Training Dataset? | Current IrrigaSense Source | Currently Available? | Automated? | Requires New Integration? | Farmer Input Required? | Five-Class Taxonomy Status | Recommended Action |
|:---|:---:|:---|:---:|:---:|:---:|:---:|:---|:---|
| `soil_moisture` | **YES** (Rank 1) | **None** | **NO** | — | **YES** | **NO** (Do NOT ask farmer) | **3. REQUIRES NEW AUTOMATED DATA SOURCE** | Current IrrigaSense does not yet have a live soil-moisture data source. Investigate automated remote sensing/API options in Milestone 7D. |
| `ec` | **YES** (Rank 2) | **None** | **NO** | — | **YES** | **NO** (Do NOT ask farmer) | **3. REQUIRES NEW AUTOMATED DATA SOURCE** | EC is present in the training dataset but is not currently available from the implemented SoilGrids integration. Evaluate replacement with static SoilGrids edaphic properties or omission. |
| `water_vol_past_4h` | **YES** (Rank 3) | **None** | **NO** | — | **YES** | **NO** (Do NOT ask farmer) | **3. REQUIRES NEW AUTOMATED DATA SOURCE** | Requires automated irrigation telemetry/flow data and should not be requested from the farmer. Default to 0.0 or exclude in purely advisory software deployment. |
| `weather_temp` | **YES** | Open-Meteo (`temperature_2m`) | **YES** | **YES** | **NO** | **NO** | **1. CURRENTLY AVAILABLE** | Direct automated bridge from `WeatherProfile.temperature_c` to ANFIS input vector. |
| `weather_radiation` | **YES** | Open-Meteo (supported by API catalog, but not queried) | **NO** | Can be automated | **MINOR** (API query expansion) | **NO** | **3. REQUIRES NEW AUTOMATED DATA SOURCE** | Add `shortwave_radiation_instant` or `direct_radiation` to Open-Meteo query params in a future milestone, or substitute with `et0_mm`. |
| `weather_wind_speed` | **YES** | Open-Meteo (`wind_speed_10m`) | **YES** | **YES** | **NO** | **NO** | **1. CURRENTLY AVAILABLE** | Direct automated bridge from `WeatherProfile.wind_speed_kmh` to ANFIS input vector. |
| `weather_humidity` | **YES** | Open-Meteo (`relative_humidity_2m`) | **YES** | **YES** | **NO** | **NO** | **1. CURRENTLY AVAILABLE** | Direct automated bridge from `WeatherProfile.humidity_percent` to ANFIS input vector. |
| `weather_pressure` | **YES** | Open-Meteo (supported by API catalog, but not queried) | **NO** | Can be automated | **MINOR** (API query expansion) | **NO** | **3. REQUIRES NEW AUTOMATED DATA SOURCE** / **5. NOT SUITABLE** | Low permutation importance (+0.000912). Prune from deployment model to avoid rule explosion, or expand Open-Meteo query to fetch `surface_pressure`. |
| `ph` | **YES** | SoilGrids (`phh2o_0-5cm_mean`) | **YES** | **YES** | **NO** | **NO** | **1. CURRENTLY AVAILABLE** | Direct automated bridge from `SoilProfile.ph` to ANFIS input vector (with optional farmer lab report override if available). |
| `hour` | **YES** | Local/Server System Datetime | **YES** | **YES** | **NO** | **NO** | **2. CAN BE DERIVED FROM EXISTING DATA** | Compute directly from local timezone clock at assessment request time (`datetime.now().hour`). |
| `weather_rain` | **YES** | Open-Meteo (`precipitation`) | **YES** | **YES** | **NO** | **NO** | **1. CURRENTLY AVAILABLE** | Available via `WeatherProfile.precipitation_mm`. (Pruned in 7B due to negative permutation importance in dry season, but available for agronomic thresholding). |
| `soil_temperature_0-7cm` | **YES** | None | **NO** | — | **NO** (Pruned) | **NO** | **5. NOT SUITABLE FOR DEPLOYMENT** | Pruned in Milestone 7B due to direct collinearity with `weather_temp` ($r = 0.9585$). Avoids requiring physical probe hardware. |
| `soil_temperature_7-18cm` | **YES** | None | **NO** | — | **NO** (Pruned) | **NO** | **5. NOT SUITABLE FOR DEPLOYMENT** | Pruned in Milestone 7B due to negative permutation importance ($-0.0040$) and chronological overfitting. |
| `irrigation_duration_minutes` | **YES** | None | **NO** | — | **NO** (Pruned) | **NO** | **5. NOT SUITABLE FOR DEPLOYMENT** | Pruned in Milestone 7B due to deployment paradox: IrrigaSense issues advisories *before* irrigating. Valve duration is unknown/zero at advisory time. |
| `et0_mm` | **NO** | Open-Meteo (`et0_fao_evapotranspiration`) | **YES** | **YES** | **NO** | **NO** | **1. CURRENTLY AVAILABLE** | Crucial agronomic parameter combining radiation, temperature, wind, and humidity. Available in IrrigaSense though absent from Mendeley dataset. |
| `nitrogen` | **NO** | SoilGrids (`nitrogen_0-5cm_mean`) | **YES** | **YES** | **NO** | **NO** | **1. CURRENTLY AVAILABLE** | Edaphic nutrient context; not in Mendeley dataset. Useful for crop vigor adjustments. |
| `organic_carbon` | **NO** | SoilGrids (`soc_0-5cm_mean`) | **YES** | **YES** | **NO** | **NO** | **1. CURRENTLY AVAILABLE** | Key determinant of soil water retention and structure; available in SoilGrids. |
| `sand_percent` | **NO** | SoilGrids (`sand_0-5cm_mean`) | **YES** | **YES** | **NO** | **NO** | **1. CURRENTLY AVAILABLE** | Physical texture fraction; allows estimation of Field Capacity (FC) and Permanent Wilting Point (PWP). |
| `silt_percent` | **NO** | SoilGrids (`silt_0-5cm_mean`) | **YES** | **YES** | **NO** | **NO** | **1. CURRENTLY AVAILABLE** | Physical texture fraction; available in SoilGrids. |
| `clay_percent` | **NO** | SoilGrids (`clay_0-5cm_mean`) | **YES** | **YES** | **NO** | **NO** | **1. CURRENTLY AVAILABLE** | Primary driver of Available Water Capacity (AWC) and cation exchange; available in SoilGrids. |
| `bulk_density` | **NO** | SoilGrids (`bdod_0-5cm_mean`) | **YES** | **YES** | **NO** | **NO** | **1. CURRENTLY AVAILABLE** | Physical soil density; essential for pedotransfer calculations. |
| `crop` | **YES** (Categorical) | Farmer Input (Q2) | **YES** | Farmer | **NO** | **YES** (Already in Q2) | **4. REQUIRES FARMER INPUT** (Existing) | Used for crop-specific water requirements and phenological stage lookup ($K_c$). |
| `planting_date` | **NO** | Farmer Input (Q3) | **YES** | Farmer | **NO** | **YES** (Already in Q3) | **4. REQUIRES FARMER INPUT** (Existing) | Derives crop growth stage and days after planting (DAP). |
| `farm_size` | **NO** | Farmer Input (Q4) | **YES** | Farmer | **NO** | **YES** (Already in Q4) | **4. REQUIRES FARMER INPUT** (Existing) | Scales depth recommendations (mm) to plot volume (liters or $m^3$). |
| `irrigation_method` | **NO** | Farmer Input (Q5) | **YES** | Farmer | **NO** | **YES** (Already in Q5) | **4. REQUIRES FARMER INPUT** (Existing) | Governs system application efficiency (e.g., drip 90%, flood 50%). |
| `water_availability` | **NO** | Farmer Input (Q6) | **YES** | Farmer | **NO** | **YES** (Already in Q6) | **4. REQUIRES FARMER INPUT** (Existing) | Imposes operational window constraints on irrigation scheduling. |

---

## 4. ANFIS Feature Groups

Based on the audit, the features are categorized into three conceptual groups to structure future ANFIS deployment architectures:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ANFIS FEATURE GROUP CLASSIFICATION                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  GROUP A: Available Automated APIs                                          │
│  ├─ weather_temp         (Open-Meteo: temperature_2m)                        │
│  ├─ weather_humidity     (Open-Meteo: relative_humidity_2m)                  │
│  ├─ weather_wind_speed   (Open-Meteo: wind_speed_10m)                       │
│  ├─ weather_rain         (Open-Meteo: precipitation)                        │
│  ├─ ph                   (ISRIC SoilGrids: phh2o_0-5cm_mean)                │
│  ├─ hour                 (System Datetime / Local Timezone)                 │
│  └─ [et0_mm, sand, silt, clay, bulk_density, organic_carbon, nitrogen]      │
│                                                                             │
│  GROUP B: Requires Additional Automated Telemetry / Expansion               │
│  ├─ soil_moisture        (Live volumetric root-zone moisture — CRITICAL GAP) │
│  ├─ ec                   (Soil electrical conductivity — CRITICAL GAP)       │
│  ├─ water_vol_past_4h    (Preceding 4-hour water applied — TELEMETRY GAP)   │
│  ├─ weather_radiation    (Open-Meteo API parameter expansion: shortwave)    │
│  └─ weather_pressure     (Open-Meteo API parameter expansion: surface_pres) │
│                                                                             │
│  GROUP C: Not Suitable for Deployed ANFIS                                   │
│  ├─ soil_temperature_0-7cm        (Collinear with weather_temp; r = 0.9585) │
│  ├─ soil_temperature_7-18cm       (Negative permutation importance; drag)   │
│  ├─ irrigation_duration_minutes   (Deployment paradox; unknown before adv.) │
│  └─ [target_point_24h, water_vol_to_24h, real_moisture_delta] (Leakage)     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Group Profiles:

### GROUP A: Features Already Available Through Existing Automated APIs
These features require zero code changes to external integrations and zero farmer interaction:
- **`weather_temp`**: Provided directly by `OpenMeteoService.parse_weather_profile()` as `temperature_c`.
- **`weather_humidity`**: Provided directly as `humidity_percent`.
- **`weather_wind_speed`**: Provided directly as `wind_speed_kmh`.
- **`weather_rain`**: Provided directly as `precipitation_mm`.
- **`ph`**: Provided directly by `SoilGridsService.fetch_all_soil_properties()` as `ph`.
- **`hour`**: Easily derived from client request timestamp or server datetime.
- **Production Enhancers (Group A+):** IrrigaSense also possesses `et0_mm` (Open-Meteo) and full particle size distributions (`sand_percent`, `clay_percent`, `silt_percent`, `bulk_density`), which represent powerful physical priors for soil hydrology.

### GROUP B: Features Requiring Additional Automated Telemetry / API Expansion
These features are absent from the current production pipeline and require targeted technical solutions:
- **`soil_moisture`**: The strongest predictor from Milestone 7B. IrrigaSense does not currently interface with any in-situ soil moisture sensor or satellite soil moisture API.
- **`ec`**: The second strongest predictor from Milestone 7B. ISRIC SoilGrids does not provide electrical conductivity coverages.
- **`water_vol_past_4h`**: Requires hardware flowmeter telemetry or a persistent software state engine tracking executed irrigations.
- **`weather_radiation`**: Not queried in current Open-Meteo client, though available in Open-Meteo's catalog.
- **`weather_pressure`**: Not queried in current Open-Meteo client, though available in Open-Meteo's catalog.

### GROUP C: Features That Should Not Be Used in the Deployed ANFIS
These features must be permanently excluded from deployment consideration:
- **`soil_temperature_0-7cm`**: 95.85% collinear with `weather_temp`. Adding in-ground sensor hardware to collect this provides near-zero incremental information while dramatically increasing hardware failure points.
- **`soil_temperature_7-18cm`**: Exhibited negative permutation importance on the chronological validation set ($-0.0040$), indicating it induces overfitting to the training partition's local seasonal trend.
- **`irrigation_duration_minutes`**: Represents concurrent valve-open time during a measurement window. Because IrrigaSense provides an advisory *ahead* of time, valve duration is either zero or undetermined at decision time.
- **Target Leakage Fields (`target_point_24h`, `water_vol_to_24h`, `real_moisture_delta`)**: Strictly prohibited forward-looking variables.

---

## 5. Critical Gap Verification Statements

The codebase audit officially establishes three verified statements regarding production gaps:

### 5.1 Soil Moisture Gap Verification
> **Audit Finding:**  
> **"Current IrrigaSense does not yet have a live soil-moisture data source."**  
> Neither the Google Maps, Open-Meteo, nor SoilGrids services query or return volumetric soil moisture. Furthermore, the frontend assessment contains no sensor input field. A live soil moisture feed does not exist in the repository.

### 5.2 Electrical Conductivity (EC) Gap Verification
> **Audit Finding:**  
> **"EC is present in the training dataset but is not currently available from the implemented SoilGrids integration."**  
> Inspection of `backend/app/services/environment/soilgrids.py` verifies that SoilGrids WCS coverages queried are restricted to `phh2o`, `nitrogen`, `soc`, `sand`, `silt`, `clay`, and `bdod`. ISRIC SoilGrids 1.0.0 global rasters do not include real-time or dynamic electrical conductivity layers.

### 5.3 Irrigation History Gap Verification
> **Audit Finding:**  
> **"Water volume history (`water_vol_past_4h`) would require automated irrigation telemetry/flow data and should not be requested from the farmer."**  
> The backend contains no IoT valve controller, pulse-flowmeter protocol, or persistent event log tracking hourly liters applied. Requesting farmers to manually log 4-hour historical liter volumes is completely unfeasible, error-prone, and violates the minimal-input design mandate.

---

## 6. Summary of Architectural Realities for Milestone 7D

| Dimension | Training Realm (Milestone 7A/7B) | Production Deployment Realm (Milestone 7C) | Gap Resolution Path |
|:---|:---|:---|:---|
| **Primary State Variable** | High-precision Campbell Scientific in-situ TDR probe (`soil_moisture`) | No live sensor probe | Investigate satellite radar (Sentinel-1/SMAP), Open-Meteo soil depth bands, or FAO-56 dual water balance |
| **Salinity / Soil Profile** | In-situ probe `ec` (µS/cm) | Static ISRIC SoilGrids texture & pH | Substitute static SoilGrids texture (clay, sand, bulk density) or omit EC |
| **Antecedent Water Log** | High-precision inline flowmeter (`water_vol_past_4h`) | Advisory software without hardware telemetry | Assume zero antecedent pulse, or track software advisory history |
| **Atmospheric Drivers** | On-site Campbell Scientific weather station | Real-time Open-Meteo API | Add `shortwave_radiation` to Open-Meteo query; leverage `et0_mm` |
| **Farmer Experience** | N/A (Fully instrumented research station) | Six simple, intuitive questions on mobile/web UI | Strictly preserve zero-hardware, zero-sensor farmer workflow |

*This audit document serves as the verified baseline for the ANFIS Deployment Strategy Report (`anfis_deployment_strategy.md`).*
