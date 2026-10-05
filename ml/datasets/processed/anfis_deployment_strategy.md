# IrrigaSense — ANFIS Production Deployment Strategy Report

> **Milestone 7C Technical Specification & Deployment Roadmap**  
> **Target Dataset:** `ml/datasets/processed/irrigation_anfis_dataset.csv` (47,007 rows)  
> **Milestone Reference:** `ml/datasets/processed/production_feature_availability.md`  
> **Core Constraint:** Minimal farmer input. The six-question farmer workflow is strictly fixed.  
> **Status:** Strategic Analysis. (No ANFIS implementation, no fuzzy membership creation, and no model training executed in this milestone).

---

## 1. Current Production Data Sources

The IrrigaSense production platform currently aggregates data through three automated services and one streamlined farmer onboarding interface:

```
                               ┌────────────────────────────────────────────────────────┐
                               │             IRRIGASENSE RUNTIME ARCHITECTURE           │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
             ┌────────────────────────────┬───────────────┴───────────────┬────────────────────────────┐
             ▼                            ▼                               ▼                            ▼
  ┌──────────────────────┐   ┌─────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
  │   GOOGLE MAPS API    │   │     OPEN-METEO API      │   │    ISRIC SOILGRIDS WCS    │   │  6-QUESTION FARMER FLOW   │
  ├──────────────────────┤   ├─────────────────────────┤   ├───────────────────────────┤   ├───────────────────────────┤
  │ • latitude           │   │ • temperature_c         │   │ • ph                      │   │ • Q1: Location (confirm)  │
  │ • longitude          │   │ • humidity_percent      │   │ • nitrogen                │   │ • Q2: Crop type           │
  │ • place_name         │   │ • precipitation_mm      │   │ • organic_carbon          │   │ • Q3: Planting date       │
  │                      │   │ • wind_speed_kmh        │   │ • sand_percent            │   │ • Q4: Farm size           │
  │                      │   │ • et0_mm (FAO-56)       │   │ • silt_percent            │   │ • Q5: Irrigation method   │
  │                      │   │                         │   │ • clay_percent            │   │ • Q6: Water availability  │
  │                      │   │                         │   │ • bulk_density            │   │                           │
  └──────────────────────┘   └─────────────────────────┘   └───────────────────────────┘   └───────────────────────────┘
```

1. **Google Maps Geolocation Service (`frontend/src/components/questions/LocationQuestion.tsx`)**:
   Provides validated coordinates (`latitude`, `longitude`) and administrative `place_name`. Serves as the spatial anchor for all environmental queries.
2. **Open-Meteo Weather Service (`backend/app/services/environment/open_meteo.py`)**:
   Provides real-time atmospheric variables: 2m air temperature (`temperature_c`), relative humidity (`humidity_percent`), precipitation (`precipitation_mm`), 10m wind speed (`wind_speed_kmh`), and reference evapotranspiration (`et0_mm` FAO-56).
3. **ISRIC SoilGrids 1.0.0 Web Coverage Service (`backend/app/services/environment/soilgrids.py`)**:
   Provides global 250m gridded edaphic characteristics for the 0–5cm layer: `ph`, `nitrogen`, `organic_carbon`, `sand_percent`, `silt_percent`, `clay_percent`, and `bulk_density`.
4. **Farmer Assessment Workflow (`frontend/src/assessment/assessmentConfig.ts`)**:
   Collects six essential operational constraints: farm location confirmation, crop cultivar, planting date (phenology stage), plot acreage, irrigation delivery system, and water availability schedule.

---

## 2. Training vs. Deployment Feature Mismatch

A fundamental disconnect exists between the academic training environment and the operational production environment:

| Dimension | Training Features (Mendeley Dataset) | Deployment Features (IrrigaSense Runtime) | Architectural Mismatch Impact |
|:---|:---|:---|:---|
| **Data Environment** | Fully instrumented research facility with research-grade Campbell Scientific hardware. | Cloud-native agronomic software serving smallholder farmers via smartphone/web. | Research sensors cannot be assumed to exist on production farms. |
| **Soil Moisture** | Direct, continuous, 10-minute in-situ TDR probe readings (`soil_moisture`). | **Absent.** No in-ground probe feed implemented. | **Extreme:** `soil_moisture` was the primary driver ($r = 0.9640$, $\Delta R^2 = 1.611$). |
| **Salinity / EC** | Direct, in-situ electrical conductivity probe readings (`ec`). | **Absent.** SoilGrids does not provide EC coverages. | **Significant:** `ec` was the secondary driver ($r = 0.5916$, $\Delta R^2 = 0.164$). |
| **Water History** | In-line pulse flowmeters logging liters every 10 min (`water_vol_past_4h`). | **Absent.** No IoT valve telemetry installed. | **Moderate:** Operational feedback loop is missing. |
| **Atmospheric State** | On-site agrometeorological tower. | Open-Meteo Live API. | **Low:** Good parity for temperature, humidity, wind, and rain; radiation requires query expansion. |
| **Agronomic Context** | Limited to 4 test crops; no soil texture or nitrogen measured. | Rich SoilGrids physical texture (sand/silt/clay), ET₀, crop phenology, and farm acreage. | **Advantage for Deployment:** IrrigaSense has macro-agronomic context absent in the Mendeley set. |

> **Critical Principle:** Machine learning models trained on sensor-rich datasets cannot be directly deployed if their key input signals do not exist at runtime. We must design a data bridge rather than naively expecting deployment inputs to mirror training columns.

---

## 3. The Soil Moisture Gap

### 3.1 Empirical Status
In Milestone 7B, `soil_moisture` was identified as overwhelmingly the most critical input:
- **Pearson Correlation ($r$):** $+0.9640$
- **Spearman Rank Correlation ($\rho$):** $+0.9512$
- **Mutual Information ($I(X; Y)$):** $1.8515$ nats
- **Validation Permutation Importance ($\Delta R^2$):** $+1.6113$ (accounted for 93.6% of native tree Gini importance)

### 3.2 Production Verification
**"Current IrrigaSense does not yet have a live soil-moisture data source."**
The codebase contains zero sensor drivers, zero IoT telemetry protocols, and zero satellite soil moisture API clients.

### 3.3 Why Asking the Farmer is Strictly Forbidden
Under the core requirements of IrrigaSense, farmers cannot and must not be asked to input soil moisture:
1. **Physical Impossibility:** Farmers cannot visually or tactilely determine root-zone volumetric moisture content with the quantitative precision (e.g., $24.7\%$ vs $31.2\%$) required by fuzzy membership functions.
2. **Subjective Noise:** Qualitative descriptions (e.g., "moist", "slightly dry") suffer from severe subjective bias and non-stationary calibration across soil textures (sandy soil feels dry at $12\%$, while clay feels dry at $22\%$).
3. **UX Degradation:** Asking farmers to purchase and read moisture probes violates the core mission of IrrigaSense: delivering high-value agronomic advisories to smallholders without expensive upfront capital.

### 3.4 Automated Non-Invasive Solutions to Investigate
To bridge this gap without farmer hardware or input, three automated pathways warrant technical investigation:
1. **Open-Meteo Soil Moisture Endpoints (Reanalysis / NWP Models):**
   Open-Meteo's weather models (e.g., ECMWF IFS, ERA5-Land, GFS) provide numerical surface and root-zone soil moisture variables (`soil_moisture_0_to_7cm_mean`, `soil_moisture_7_to_28cm_mean`, etc.) in $m^3/m^3$. Ingesting this via the existing Open-Meteo service would maintain zero farmer burden and zero additional infrastructure cost.
2. **Satellite Remote Sensing APIs:**
   Public Earth Observation data from Copernicus Sentinel-1 (C-band Synthetic Aperture Radar, 1km resolution) or NASA SMAP (L-band Radiometer, 3–9km resolution) provide automated topsoil moisture retrievals.
3. **Continuous Hydrological Water Balance Model (FAO-56 Dual Bucket):**
   A software-driven daily root-zone soil water depletion model:
   $$D_{r,i} = D_{r,i-1} - (P_i - RO_i) - I_i - CR_i + ET_{c,i} + DP_i$$
   Using Open-Meteo precipitation ($P$) and reference evapotranspiration ($ET_0$), SoilGrids available water capacity ($AWC$ derived from sand/clay), and crop coefficient curves ($K_c$), IrrigaSense can simulate daily soil moisture depletion internally without external sensors.

---

## 4. The Electrical Conductivity (EC) Gap

### 4.1 Empirical Status
In Milestone 7B, `ec` emerged as the second strongest predictor:
- **Pearson Correlation ($r$):** $+0.5916$
- **Spearman Rank Correlation ($\rho$):** $+0.5175$
- **Validation Permutation Importance ($\Delta R^2$):** $+0.1643$

### 4.2 Production Verification
**"EC is present in the training dataset but is not currently available from the implemented SoilGrids integration."**
ISRIC SoilGrids 1.0.0 provides static soil properties (pH, organic carbon, clay, sand, silt, bulk density, nitrogen). It does not provide dynamic electrical conductivity or soluble salt concentration.

### 4.3 Analysis of EC's Role in Training
A critical insight from the dataset audit is that `ec` in the Mendeley dataset was **not** acting primarily as a rapidly changing dynamic weather variable, but rather as an **edaphic fingerprint of the experimental zones**:
- **Zone 1 & 2 (Open field tomato):** Low baseline EC ($\approx 150$–$250\ \mu\text{S/cm}$).
- **Zone 3 (Potted tomato):** Elevated EC ($\approx 400$–$700\ \mu\text{S/cm}$) due to continuous concentrated fertigation salts in containers.
- **Zone 4 (Zucchini):** Distinct intermediate baseline ($\approx 250$–$350\ \mu\text{S/cm}$).
- **Zone 5 (Blueberry):** Distinct high-acidity/salinity regime ($\approx 350$–$500\ \mu\text{S/cm}$).

Because the training dataset lacked categorical soil texture or cation exchange capacity, the tree models and correlation metrics leveraged `ec` to distinguish between soil environments.

### 4.4 Resolution Strategy
1. **Do NOT ask the farmer:** Farmers do not own electrical conductivity probes.
2. **Surrogate Replacement with SoilGrids Edaphic Properties:** In production, IrrigaSense already has SoilGrids particle size fractions (`clay_percent`, `sand_percent`, `bulk_density`) and `ph`. These physical properties classify the soil type far more rigorously than raw EC.
3. **Omission in Parsimonious Models:** In Milestone 7D, we will evaluate ANFIS architectures trained without `ec` to measure whether the remaining automated variables maintain acceptable accuracy.

---

## 5. The Irrigation History Gap (`water_vol_past_4h`)

### 5.1 Empirical Status
In Milestone 7B, `water_vol_past_4h` ranked 3rd in correlation ($r = 0.1979$, $\rho = 0.3010$, MI $= 0.6082$), capturing the infiltration pulse of water recently applied.

### 5.2 Production Verification
**"Water volume history (`water_vol_past_4h`) would require automated irrigation telemetry/flow data and should not be requested from the farmer."**
IrrigaSense does not connect to smart valve flowmeters or pulse counters.

### 5.3 Why Asking the Farmer is Forbidden
- Farmers do not keep hourly stopwatch logs or cubic-meter flow measurements.
- Asking a farmer "How many liters of water were applied across your field in the past 4 hours?" is impossible for them to answer accurately, especially for furrow or flood irrigation methods.

### 5.4 Resolution Strategy
1. **Advisory Pre-Condition Assumption ($water\_vol\_past\_4h = 0$):**
   In real-world advisory usage, a farmer opens IrrigaSense **before** turning on the pump. Therefore, in the vast majority of advisory requests, no irrigation has occurred in the past 4 hours ($water\_vol\_past\_4h = 0$).
2. **Software Event Logging:**
   When IrrigaSense issues an advisory and the farmer marks it as "Applied", the application's relational database can record the timestamped volume. Future queries can sum recent applied volumes automatically without farmer prompts.
3. **Omission from Core Model:**
   Milestone 7B permutation importance for `water_vol_past_4h` was modest ($+0.000366$). Training an ANFIS without this operational feature is viable and reduces rule complexity.

---

## 6. Crop Generalization Limitation

The Mendeley training dataset is restricted to four crops across five experimental zones:
1. **Tomato, open field** (Zones 1 & 2)
2. **Tomato, potted containers** (Zone 3)
3. **Zucchini** (Zone 4)
4. **Blueberry** (Zone 5)

### Fundamental Scientific Limitation:
> **No Demonstrated Cross-Crop Generalization:**  
> The training dataset provides zero empirical data for major commercial crops supported by IrrigaSense (such as **sugarcane, cotton, wheat, onion, gram, soybean, and maize**). Under no circumstances can we claim that an ANFIS trained on this dataset will generalize reliably to crops outside this 4-crop envelope.

### Physiological & Hydrological Drivers of Crop Specificity:
- **Rooting Depth ($Z_r$):** Blueberry roots are shallow ($0.2$–$0.4\text{ m}$), whereas sugarcane roots penetrate deeply ($1.2$–$2.0\text{ m}$), altering the effective soil reservoir volume.
- **Crop Coefficient ($K_c$):** Water demand curves vary dramatically across phenological stages (e.g., initial, mid-season, late-season), scaling reference $ET_0$ into actual crop water demand $ET_c$.
- **Depletion Fraction ($p$):** Crop sensitivity to water stress dictates the allowable soil moisture deficit before yield reduction occurs.

### Architectural Mitigation:
The deployed system must not rely solely on raw empirical data for unrepresented crops. Instead, it must utilize a **hybrid neuro-fuzzy architecture**: using ANFIS for empirical soil-atmospheric dynamics while scaling recommendations through standardized FAO-56 crop coefficients ($K_c$) and crop-specific management allowable depletion ($MAD$) thresholds based on the farmer's selected crop (Q2) and planting date (Q3).

---

## 7. Production Feature Strategies

Three distinct deployment strategies are formulated. In accordance with project instructions, none is declared universally superior; each presents specific trade-offs across data availability, engineering overhead, and model accuracy.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PRODUCTION FEATURE DEPLOYMENT STRATEGIES                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  STRATEGY A: Existing APIs Only                                                        │
│  ├─ Data: Open-Meteo + SoilGrids + 6 Farmer Questions                                  │
│  ├─ Available: weather_temp, weather_humidity, weather_wind_speed, weather_rain,       │
│  │             ph, hour, et0_mm, sand, clay, silt, bulk_density, crop, DAP, method     │
│  ├─ Missing: soil_moisture, ec, water_vol_past_4h, weather_radiation                  │
│  └─ Profile: Zero cost, immediate readiness, requires reframing ANFIS target/inputs    │
│                                                                                        │
│  STRATEGY B: Existing APIs + Automated Soil-Moisture Data                               │
│  ├─ Data: Open-Meteo (+ rad & soil moisture) + SoilGrids + 6 Farmer Questions          │
│  ├─ Available: All Strategy A + automated soil_moisture + weather_radiation            │
│  ├─ Missing: ec (proxied by SoilGrids), water_vol_past_4h (assumed 0 or logged)        │
│  └─ Profile: Best software balance, preserves core ANFIS architecture, zero farmer IoT │
│                                                                                        │
│  STRATEGY C: Existing APIs + In-Situ IoT Sensors & Flowmeters                          │
│  ├─ Data: Open-Meteo + SoilGrids + Farmer Flow + In-field TDR & Flowmeter Telemetry    │
│  ├─ Available: 100% feature match with Mendeley training dataset                       │
│  ├─ Missing: None                                                                      │
│  └─ Profile: Maximum theoretical accuracy, prohibitive hardware cost & maintenance     │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Strategy A: Existing APIs Only (Pure Software — Zero Added Services)

- **Available Features:**
  - Automated Weather: `weather_temp`, `weather_humidity`, `weather_wind_speed`, `weather_rain`, `et0_mm` (Open-Meteo)
  - Automated Soil: `ph`, `sand_percent`, `clay_percent`, `silt_percent`, `bulk_density`, `organic_carbon`, `nitrogen` (SoilGrids)
  - Derived Time: `hour` (System clock)
  - Farmer Inputs: `crop`, `planting_date`, `farm_size`, `irrigation_method`, `water_availability`
- **Missing Features:**
  - `soil_moisture` (no live in-situ or satellite probe)
  - `ec` (SoilGrids provides texture, not EC)
  - `water_vol_past_4h` (no flowmeters)
  - `weather_radiation` (not currently requested in `open_meteo.py`)
  - `weather_pressure` (not currently requested)
- **Advantages:**
  - **Zero Implementation Delay:** 100% supported by the existing, tested codebase.
  - **Zero Infrastructure Cost:** Completely free from hardware dependencies or paid API subscriptions.
  - **Zero Farmer Burden:** Preserves the clean six-question UX without adding a single question.
- **Limitations:**
  - Cannot run the exact ANFIS models trained in Milestone 7B (Set B or Set C) because the primary state variable (`soil_moisture`) is missing.
  - Must reframe the prediction task: rather than forecasting next-day soil moisture from today's sensor reading, the system must predict irrigation water requirement ($ET_c$ deficit) directly from weather and soil texture.
- **Effect on ANFIS Design:**
  - ANFIS architecture must be re-trained using atmospheric and edaphic inputs available in production: e.g., Inputs = [`et0_mm`, `temperature_c`, `humidity_percent`, `clay_percent`, `sand_percent`].

---

### Strategy B: Existing APIs + Automated Soil-Moisture & Radiation Data (Software-First Remote Ingestion)

- **Available Features:**
  - All Strategy A features (`weather_temp`, `weather_humidity`, `weather_wind_speed`, `weather_rain`, `et0_mm`, `ph`, SoilGrids texture).
  - **Automated `soil_moisture`:** Ingested via Open-Meteo soil depth layers (`soil_moisture_0_to_7cm_mean`) or satellite Copernicus/SMAP service.
  - **Automated `weather_radiation`:** Added by requesting `shortwave_radiation_instant` from Open-Meteo.
  - **Derived `hour`:** Local system clock.
- **Missing Features:**
  - `ec` (Substituted by SoilGrids physical texture fractions: `clay_percent`, `sand_percent`).
  - `water_vol_past_4h` (Defaulted to $0.0$ at advisory request time, or tracked via internal application log).
- **Advantages:**
  - **Preserves Core ANFIS Paradigm:** Restores the primary state variable (`soil_moisture`), enabling near-direct application of the high-performing Set B / Set C ANFIS architectures ($R^2 \approx 0.908$).
  - **Completely Hardware-Free:** Farmers require zero IoT probes or flowmeters.
  - **High Scalability:** Operates globally anywhere Google Maps coordinates are provided.
- **Limitations:**
  - Automated gridded/satellite soil moisture represents topsoil ($0$–$7\text{ cm}$) and has spatial resolution limits ($1\text{ km}$ to $10\text{ km}$) compared to physical root-zone probe measurements.
  - Requires updating `OpenMeteoService` in a future milestone to parse additional weather/soil variables.
- **Effect on ANFIS Design:**
  - ANFIS can utilize a 4-to-6 input architecture: e.g., [`soil_moisture`, `weather_temp`, `weather_radiation`, `weather_humidity`, `clay_percent`].

---

### Strategy C: Existing APIs + In-Situ IoT Sensors & Flowmeters (Full Physical Instrumentation)

- **Available Features:**
  - 100% complete feature match with the training dataset:
  - Live root-zone `soil_moisture` from in-field capacitive/TDR probe.
  - Live root-zone `ec` from in-field sensor.
  - Live antecedent irrigation volume `water_vol_past_4h` from in-line pulse flowmeters.
  - Live on-site microclimate (`weather_temp`, `weather_radiation`, `weather_wind_speed`, `weather_humidity`, `weather_pressure`).
  - Existing SoilGrids edaphic profile and farmer assessment context.
- **Missing Features:** None.
- **Advantages:**
  - **Exact 1-to-1 Match with Training Set:** Permits direct deployment of the Set B (8 inputs) or Set C (5 inputs) ANFIS models trained in Milestone 7B with zero architectural translation loss.
  - **Maximum Micro-Precision:** Reflects exact real-time root-zone dynamics and localized plot wetting fronts.
  - **Autonomous Closed-Loop Capability:** Enables automated valve triggering without manual farmer intervention.
- **Limitations:**
  - **Prohibitive Hardware Cost:** IoT probes, flowmeters, microcontrollers, and solar/battery units cost \$150–\$500+ per field, making it inaccessible for the vast majority of target smallholder farmers.
  - **High Maintenance Overhead:** Soil probe drift, salt encrustation, wire damage from tilling, and telemetry dropout in rural connectivity dead-zones.
  - **Violates IrrigaSense Software-First Philosophy:** Transforms an accessible mobile web advisory tool into a complex hardware integration project.
- **Effect on ANFIS Design:**
  - No adaptation needed. Direct 1-to-1 execution of the Milestone 7B Set B ($2^8 = 256$ rules or FCM clusters) or Set C ($2^5 = 32$ rules) ANFIS models.

---

## 8. Summary Comparison of Deployment Strategies

| Strategic Attribute | Strategy A (Existing APIs Only) | Strategy B (Existing APIs + Automated Moisture) | Strategy C (IoT Hardware Instrumentation) |
|:---|:---:|:---:|:---:|
| **Capital Cost to Farmer** | **\$0.00** (Completely Free) | **\$0.00** (Completely Free) | **\$150 – \$500+** per field |
| **Farmer Data Entry Burden** | **Zero** (6 simple questions) | **Zero** (6 simple questions) | **Zero** (automated telemetry) |
| **New Service Integrations Needed** | **None** (Existing code) | **Minor** (Open-Meteo param expansion) | **Extensive** (IoT gateway, MQTT/HTTP) |
| **Parity with Mendeley Training Features** | Low (Missing `soil_moisture` & `ec`) | High (Restores `soil_moisture` & radiation) | **100% Exact Match** |
| **ANFIS Model Adaptations Required** | Must reformulate inputs around $ET_0$ & soil | Minor (Omit EC or replace with clay/sand) | None (Direct Set B/C deployment) |
| **Target Audience Suitability** | Smallholders, regional advisory | Smallholders, progressive farmers | Commercial agribusiness, research stations |

---

## 9. Recommended Next Technical Investigation (for Milestone 7D)

To prepare for subsequent milestones without violating project constraints, the following technical investigations are recommended:

1. **Evaluate Open-Meteo Soil Moisture Endpoints:**
   Inspect Open-Meteo's API documentation for `soil_moisture_0_to_7cm_mean` and `soil_moisture_7_to_28cm_mean`. Benchmark their data availability, latitudinal coverage, and latency against the coordinates of verified agricultural zones (e.g., Baramati: $18.155^\circ\text{N}, 74.580^\circ\text{E}$).
2. **Empirical Ablation of Missing Features on Master Dataset:**
   Conduct a targeted ablation study on `ml/datasets/processed/irrigation_anfis_dataset.csv`:
   - Fit baseline regressors on **Strategy A features** (weather variables only + soil pH) and quantify the drop in $R^2$ compared to Set B.
   - Fit models on **Strategy B features** (`soil_moisture` + weather variables + soil pH, omitting `ec` and `water_vol_past_4h`) to evaluate if $R^2 \ge 0.88$ is maintained.
3. **Open-Meteo Weather Parameter Expansion Prototype:**
   Test adding `shortwave_radiation_instant` and `surface_pressure` to the Open-Meteo request parameters in `open_meteo.py` without modifying the core `WeatherProfile` contract, verifying response reliability.
4. **Formulate FAO-56 Dual Crop Coefficient Water Balance Architecture:**
   Investigate coupling ANFIS with a daily root-zone soil water depletion model ($D_{r,i}$) where SoilGrids supplies $AWC$ (Available Water Capacity) and Open-Meteo supplies daily $ET_0$.

---

## 10. Features That Must NOT Become Farmer Questions (Blacklist)

To protect user experience, accessibility, and scientific validity, the following parameters are strictly blacklisted from ever being added to the farmer questionnaire:

| Blacklisted Feature | Why It Must NEVER Be Asked to the Farmer |
|:---|:---|
| **`soil_moisture`** | Volumetric moisture percentage cannot be measured visually or tactilely; asking produces catastrophic measurement error. |
| **`ec`** | Electrical conductivity ($\mu\text{S/cm}$) requires calibrated laboratory or field conductivity meters unavailable to smallholders. |
| **`water_vol_past_4h`** | Exact 4-hour historical liter volumes require in-line pulse flowmeters; smallholders cannot track liter increments. |
| **`weather_radiation`** | Solar irradiance ($\text{W/m}^2$) requires pyranometers; live weather APIs provide this automatically. |
| **`weather_pressure`** | Atmospheric barometric pressure ($\text{hPa}$) requires barometers; live weather APIs provide this automatically. |
| **`soil_temperature_0-7cm`** | Subsurface root-zone temperature requires thermocouple probes; highly collinear with ambient air temperature. |
| **`soil_temperature_7-18cm`** | Deep subsurface temperature requires in-ground probes; showed negative permutation importance in validation. |
| **`irrigation_duration_minutes`** | Unknown at advisory time; asking the farmer creates a circular dependency since the system's role is to advise the duration. |

---

## 11. Conclusion

Milestone 7C establishes the definitive operational boundary between empirical research findings and live production realities. By identifying the exact availability of features across Google Maps, Open-Meteo, and SoilGrids, IrrigaSense maintains strict architectural integrity: **zero unverified claims, zero new farmer burdens, and a clear roadmap for bridging the soil moisture gap in Milestone 7D.**
