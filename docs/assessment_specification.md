# IrrigaSense — Formal 6-Question Assessment Specification

> **Document ID:** `SPEC-ASSESSMENT-V2-20261010`
> **Topic:** Onboarding Questionnaire & Environmental Data Resolution Specification
> **Status:** **ACTIVE / PRODUCTION SPECIFICATION**
> **Supersedes:** Legacy 20-Question Specification (V1)

---

## 1. Assessment Philosophy & Core Principles

The IrrigaSense onboarding experience is engineered around a single foundational agronomic principle:
> **Ask the farmer only for information that cannot reliably and accurately be resolved via automated telemetry.**

### UX & Agronomic Design Principles:
1. **Zero Technical Hardware Prerequisite:** Eliminates any requirement for farmers to purchase, install, calibrate, or wire in-situ capacitive/TDR soil moisture probes.
2. **Zero Manual Mathematical Burden:** Never asks farmers to provide numerical soil physical properties (e.g. bulk density, clay percentage, field capacity) or atmospheric indices (e.g. $ET_0$, vapor pressure deficit).
3. **Frictionless 6-Question Traversal:** Restricts user input strictly to 6 intuitive, high-signal questions formatted as visual cards, date pickers, and interactive maps.
4. **Transparent Data Provenance:** Clearly separates user-provided operational context from upstream automated satellite/meteorological telemetry.
5. **Clear Visual Separation:** Google Maps satellite imagery provides visual geographic plot confirmation; it is explicitly noted that optical satellite imagery does not directly measure root-zone moisture or NDVI.

---

## 2. Onboarding Workflow & Question Architecture

The onboarding pipeline consists of **6 sequential questions (Q1–Q6)** followed by a dedicated **Review & Submission Screen (REVIEW)**:

```
[Q1: Farm Location]
         │ (Automated Telemetry Fetch: Open-Meteo + ISRIC SoilGrids)
         ▼
[Q2: Current Crop]
         │ (Maps to FAO-56 Crop Knowledge & Root Depth)
         ▼
[Q3: Planting Date]
         │ (Computes DAP & Phenological Growth Stage)
         ▼
[Q4: Farm Size]
         │ (Acreage Context)
         ▼
[Q5: Irrigation Delivery Method]
         │ (Application System Context)
         ▼
[Q6: Water Availability Security]
         │ (Water Reliability Context)
         ▼
[REVIEW: Summary & Confirmation]
         │ (Final Verification)
         ▼
[LIVE FARMER DASHBOARD]
```

---

## 3. Detailed Question Specifications

### Q1 — Farm Location (Google Maps Pinpoint)
- **Question ID:** `Q1`
- **Section:** Location (`location`)
- **Question Title:** *"Where is your farm?"*
- **Question Subtitle:** *"Pinpoint your exact farmland coordinates on the map to automatically load local weather and soil data."*
- **Input Type:** Interactive Google Maps location picker with draggable pin, search autocomplete, and manual fallback coordinates.
- **Required:** Yes (`location_confirmed === true` is required to advance).
- **Data Captured:**
  - `latitude` (`float`): Decimal degrees (e.g. `18.1550`).
  - `longitude` (`float`): Decimal degrees (e.g. `74.5800`).
  - `place_name` (`string`): Reverse-geocoded locality (e.g. *"Baramati North Farmland, Pune District, Maharashtra"*).
  - `location_confirmed` (`boolean`): Explicit user confirmation.
- **Automated Upstream Telemetry Triggered:**
  - **Open-Meteo Weather API:** Resolves air temperature at 2m (°C), relative humidity (%), precipitation (mm), wind speed (km/h), and daily FAO-56 reference evapotranspiration ($ET_0$, mm/day).
  - **Open-Meteo Root-Zone Soil Moisture:** Queries root-zone volumetric water content ($0–7\text{ cm}$ and $7–28\text{ cm}$, % VWC).
  - **ISRIC SoilGrids 250m REST/WCS:** Queries topsoil clay percentage ($0–30\text{ cm}$, % mass), soil pH, organic carbon, and bulk density.

---

### Q2 — Current Crop
- **Question ID:** `Q2`
- **Section:** Crop (`crop`)
- **Question Title:** *"What is your main crop for this field?"*
- **Question Subtitle:** *"Select your primary cultivated crop to load scientific crop coefficients and moisture depletion thresholds."*
- **Input Type:** Visual card selector with searchable catalog.
- **Supported Crops (Milestone 9/10 Catalog):**
  - **Tomato (*Solanum lycopersicum*):** Solanaceae family, Loam soil baseline, $K_c = [0.60, 1.15, 0.80]$, MAD fraction $p = 0.40$ (40%).
  - **Zucchini (*Cucurbita pepo*):** Cucurbitaceae family, Sandy Loam baseline, $K_c = [0.50, 0.95, 0.75]$, MAD fraction $p = 0.50$ (50%).
  - **Blueberry (*Vaccinium corymbosum*):** Ericaceae family, Potted/Substrate baseline, $K_c = [0.40, 1.00, 0.75]$, MAD fraction $p = 0.25$ (25%).
- **Required:** Yes.
- **Data Captured:** `crop` (`string` / crop identifier object).

---

### Q3 — Planting Date
- **Question ID:** `Q3`
- **Section:** Planting Timeline (`planting_date`)
- **Question Title:** *"When was this crop planted or transplanted?"*
- **Question Subtitle:** *"Used to determine the crop's current stage of growth and root development."*
- **Input Type:** Native HTML5 Date Picker (`YYYY-MM-DD`).
- **Validation:** Must not be a future date ($\text{planting\_date} \le \text{current\_date}$).
- **Agronomic Derivative:**
  $$\text{DAP} = \text{current\_date} - \text{planting\_date}$$
  Dynamically computes FAO-56 phenological growth stage:
  - `Initial` ($0 \le \text{DAP} < L_{\text{ini}}$)
  - `Crop Development / Vegetative` ($L_{\text{ini}} \le \text{DAP} < L_{\text{ini}} + L_{\text{dev}}$)
  - `Mid-Season / Reproductive` ($L_{\text{ini}} + L_{\text{dev}} \le \text{DAP} < L_{\text{ini}} + L_{\text{dev}} + L_{\text{mid}}$)
  - `Late-Season / Ripening` ($\text{DAP} \ge L_{\text{ini}} + L_{\text{dev}} + L_{\text{mid}}$)
- **Required:** Yes.
- **Data Captured:** `planting_date` (`string` ISO date).

---

### Q4 — Farm Size
- **Question ID:** `Q4`
- **Section:** Farm Area (`farm_size`)
- **Question Title:** *"What is the size of your cultivated farm plot?"*
- **Question Subtitle:** *"Helps understand your operational scale."*
- **Input Type:** Radio option selection.
- **Options:**
  - `< 1 acre` (Smallholder plot)
  - `1–2 acres` (Small farm)
  - `2–5 acres` (Medium commercial farm)
  - `> 5 acres` (Large commercial holding)
- **Required:** Yes.
- **Agronomic Note:** Retained strictly for operational context. The system adheres to volumetric restraint and does **not** fabricate uncalibrated liter/gallon amounts based on farm size.
- **Data Captured:** `farm_size` (`string`).

---

### Q5 — Irrigation Delivery Method
- **Question ID:** `Q5`
- **Section:** Irrigation System (`irrigation_method`)
- **Question Title:** *"How do you apply irrigation water to your field?"*
- **Question Subtitle:** *"Different methods have different water delivery efficiencies and timing dynamics."*
- **Input Type:** Radio option selection.
- **Options:**
  - `Drip Irrigation` (High efficiency, micro-emitter system)
  - `Sprinkler Irrigation` (Overhead spray application)
  - `Flood / Furrow Irrigation` (Surface flooding)
  - `Manual / Hose / Other` (Manual watering)
- **Required:** Yes.
- **Data Captured:** `irrigation_method` (`string`).

---

### Q6 — Water Availability Security
- **Question ID:** `Q6`
- **Section:** Water Supply (`water_availability`)
- **Question Title:** *"How secure and reliable is your irrigation water supply?"*
- **Question Subtitle:** *"Helps contextualize urgency and conservation recommendations."*
- **Input Type:** Radio option selection.
- **Options:**
  - `Abundant` (Canals, reliable borewell, or full storage)
  - `Moderate` (Sufficient for scheduled cycles with occasional rationing)
  - `Limited` (Restricted supply or water stress risk)
- **Required:** Yes.
- **Data Captured:** `water_availability` (`string`).

---

## 4. Review & Submission Step (REVIEW)

The **Review Screen** is rendered after Q6 completion:
- **Title:** *"Review Your Farm Profile"*
- **Purpose:** Displays an editable summary card of all 6 answers (Location, Crop, Planting Date & DAP, Farm Size, Irrigation Method, Water Availability).
- **Actions:**
  - *Edit Step:* Clicking any section navigates directly back to that question step.
  - *Confirm & Submit:* Sends assessment to backend (`POST /api/assessments`), queries the ANFIS decision engine (`POST /api/decision/recommendation`), and transitions to the live farmer dashboard.

---

## 5. Automated Environmental Telemetry Contract

When coordinates $(\text{lat}, \text{lon})$ are confirmed in Q1, the backend automatically resolves:

| Variable | Upstream Source | API Parameter / Resolution | Internal Domain Unit |
| :--- | :--- | :--- | :---: |
| **Ambient Temperature** | Open-Meteo | `current.temperature_2m` | °C |
| **Relative Humidity** | Open-Meteo | `current.relative_humidity_2m` | % |
| **Precipitation** | Open-Meteo | `current.precipitation` | mm |
| **Wind Speed** | Open-Meteo | `current.wind_speed_10m` | km/h |
| **Reference ET ($ET_0$)** | Open-Meteo | `daily.et0_fao_evapotranspiration` | mm/day |
| **Root-Zone Soil Moisture** | Open-Meteo | `current.soil_moisture_7_to_28cm` | % VWC |
| **Topsoil Clay Content** | ISRIC SoilGrids | `clay_0-30cm_mean` (250m resolution) | % mass |

> [!NOTE]
> **Satellite Imagery Disclaimer:**
> The satellite map in the dashboard renders visual optical overhead tiles from Google Maps to give the farmer geographical context and parcel orientation. It does **not** perform direct radiometric thermal sensing, NDVI computation, or physical root-zone moisture probing.

---

## 6. Backend Integration Contracts

### Assessment Persistence (`POST /api/assessments`)
```json
{
  "farm_id": 1,
  "assessment_version": "2.0.0",
  "data": {
    "location": {
      "latitude": 18.155,
      "longitude": 74.58,
      "place_name": "Baramati North Farmland, Pune District, Maharashtra",
      "location_confirmed": true
    },
    "crop": "Tomato",
    "planting_date": "2026-08-15",
    "farm_size": "2–5 acres",
    "irrigation_method": "Drip",
    "water_availability": "Moderate"
  }
}
```

### Recommendation Endpoint (`POST /api/decision/recommendation`)
The decision engine evaluates the 6-question context against the frozen ANFIS 24-hour forecast, returning a deterministic recommendation:
- `NO_IRRIGATION` (Soil moisture comfortably above MAD threshold)
- `MONITOR` (Approaching depletion boundary within 24 hours)
- `IRRIGATION_RECOMMENDED` (Predicted moisture falls below MAD threshold)
- `IRRIGATION_URGENT` (Severe depletion approaching permanent wilting point)
- `INSUFFICIENT_CONFIDENCE` (Inputs exceed validated operating domain, triggering safety guardrails)
