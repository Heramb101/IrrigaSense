# IrrigaSense Adaptive Irrigation Decision Engine

## 1. Purpose
The **Adaptive Irrigation Decision Engine** is a deterministic, crop-aware agronomic decision layer designed to translate:
1. Current environmental state (soil moisture, ET₀, temperature, relative humidity, clay content),
2. ANFIS predicted 24-hour future soil moisture (`predicted_target_mean_24h`),
3. Crop identity and growth stage (Days After Planting, FAO-56 stage boundaries),
4. Soil physical thresholds (Field Capacity, Permanent Wilting Point, Managed Allowable Depletion),
5. Irrigation delivery context (Drip, Sprinkler, Flood), and
6. On-farm water availability constraints

into a safe, transparent, and farmer-actionable irrigation recommendation.

> [!IMPORTANT]
> **Architectural Boundary:** The Decision Engine is **NOT an ML model**. It is an explainable, deterministic agronomic rule layer sitting strictly downstream of the frozen ANFIS neural-fuzzy predictor.

---

## 2. Architecture & Design Principles

### Decoupling Prediction from Decision
In naive irrigation systems, recommendations are frequently triggered by arbitrary fixed thresholds (e.g., `soil_moisture < 50%` or `< 20%`). Such heuristics fail across differing soil textures and crop species:
- A volumetric water content (VWC) of **24%** in a clay loam is **SAFE** for Zucchini ($Threshold_{MAD} = 21.0\%$), but represents an **IRRIGATION DEFICIT** for Tomato ($Threshold_{MAD} = 24.8\%$) and a **CRITICAL DESICCATION** for potted Blueberry ($Threshold_{MAD} = 38.8\%$).
- The 5-input ANFIS model predicts the **physical state** of the soil 24 hours into the future.
- The Decision Engine evaluates whether that physical state compromises the biological requirements of the specific crop at its current phenological stage.

```
+-------------------------------------------------------------------+
|               Farmer Inputs (Strict 6 Questions)                  |
| Location | Crop | Planting Date | Farm Size | Method | Water Avail|
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|             Automated Environmental Telemetry Data                |
|      Open-Meteo (ET0, Temp, RH) + SoilGrids (Clay, Moisture)      |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                 FROZEN ANFIS MODEL (5 Inputs)                     |
|  [soil_moisture, et0, temp, rh, clay] -> predicted_target_mean_24h|
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|             ADAPTIVE IRRIGATION DECISION ENGINE                   |
|  1. Domain Guardrails (Milestone 8D boundary protection)          |
|  2. Crop Profile & Phenological Stage (DAP / FAO-56 boundaries)   |
|  3. Managed Allowable Depletion (MAD) & Moisture State Evaluator  |
|  4. Delivery Context & Water Availability Adjustment              |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|              Farmer-Actionable Recommendation Object              |
| Decision | Confidence | Explanation | Agronomic Diagnostics       |
+-------------------------------------------------------------------+
```

---

## 3. Inputs

### A. Farmer Assessment Inputs (Strictly 6 Questions)
The onboarding workflow requires no sensor installations or technical inputs:
- `Q1. Farm Location`: Latitude, longitude, place name.
- `Q2. Current Crop`: Crop selection (e.g., Tomato, Zucchini, Blueberry).
- `Q3. Planting Date`: Sowing or transplant date (`YYYY-MM-DD`).
- `Q4. Farm Size`: Farm area and units (retained for contextual awareness; **no volume calculation in M9**).
- `Q5. Irrigation Method`: Delivery system (`Drip`, `Sprinkler`, `Flood`, `Other`).
- `Q6. Water Availability`: Water security level (`Abundant`, `Moderate`, `Limited`).

### B. Automated Telemetry Inputs
- `soil_moisture_root_zone`: Root zone volumetric water content (% VWC, 0–7 cm / 7–28 cm).
- `et0_fao_evapotranspiration`: FAO-56 Penman-Monteith reference evapotranspiration (mm/day).
- `temperature_2m`: Ambient air temperature (°C).
- `relative_humidity_2m`: Relative humidity (%).
- `clay_content`: Soil clay fraction (% mass).

### C. ANFIS Predictive Input
- `predicted_target_mean_24h`: Projected 24-hour mean root zone moisture (% VWC).

---

## 4. Crop Knowledge Layer (`crop_profiles.json`)

The engine references an expandable agronomic catalog in `ml/decision_engine/crop_profiles.json`. Currently implemented profiles:

| Crop ID | Crop Name | Family | Kc Stages [ini, mid, end] | MAD Fraction ($p$) | Soil Context | Root Depth (m) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `tomato` | Tomato (*Solanum lycopersicum*) | Solanaceae | 0.60, 1.15, 0.80 | 0.40 (40%) | Loam (FC: 31%, PWP: 15%) | 0.30–0.70 |
| `zucchini` | Zucchini (*Cucurbita pepo*) | Cucurbitaceae | 0.50, 0.95, 0.75 | 0.50 (50%) | Sandy Loam (FC: 26%, PWP: 11%) | 0.25–0.50 |
| `blueberry` | Blueberry (*Vaccinium corymbosum*) | Ericaceae | 0.40, 1.00, 0.75 | 0.25 (25%) | Peat/Substrate (FC: 45%, PWP: 20%) | 0.20–0.40 |

### Days After Planting (DAP) & Stage Transition
Given `planting_date` and assessment date, the engine calculates:
$$\text{DAP} = \text{current\_date} - \text{planting\_date}$$

Phenological stages are mapped dynamically according to profile stage definitions:
1. `initial`: Early germination / establishment
2. `vegetative`: Leaf canopy expansion
3. `flowering_fruit_set` / `development`: Flowering and initial fruit development
4. `mid_season`: Full canopy and yield formation
5. `late_season`: Ripening, maturation, harvest

If `planting_date` is missing or in the future, the engine sets `crop_stage = "UNKNOWN"` and enters a conservative agronomic monitoring path.

---

## 5. Managed Allowable Depletion (MAD) Logic

The engine models soil moisture using classic FAO-56 depletion dynamics:

$$\text{TAW} = \text{FC} - \text{PWP}$$
$$\text{RAW} = \text{MAD} \times \text{TAW}$$
$$\text{Threshold}_{MAD} = \text{FC} - \text{RAW}$$

Where:
- $\text{TAW}$: Total Available Water (% VWC)
- $\text{RAW}$: Readily Available Water before water stress occurs (% VWC)
- $\text{Threshold}_{MAD}$: Critical moisture boundary below which stomatal conductance declines
- $\text{Depletion Fraction } (D_f)$:
  $$D_f = \frac{\text{FC} - \theta_{24h}}{\text{FC} - \text{PWP}} = \frac{\text{FC} - \theta_{24h}}{\text{TAW}}$$

---

## 6. Moisture State Classification

Moisture states are classified relative to physical thresholds, rather than fixed universal numbers:

| State | Condition | Interpretation |
| :--- | :--- | :--- |
| `SATURATED` | $\theta_{24h} > \text{FC} \times 1.08$ | Root zone anaerobic; drainage required, zero irrigation. |
| `HIGH` | $\text{FC} \le \theta_{24h} \le \text{FC} \times 1.08$ | Moisture at or slightly above field capacity. |
| `SAFE` | $\text{Threshold}_{MAD} \le \theta_{24h} < \text{FC}$ | Soil water is readily accessible; transpiration unhindered. |
| `DEFICIT` | $\text{PWP} < \theta_{24h} < \text{Threshold}_{MAD}$ | Soil has dried past allowable depletion; crop approaching stress. |
| `SEVERE_DEFICIT` | $\theta_{24h} \le \text{PWP}$ or $D_f \ge 1.0$ | Water held tightly at wilting boundary; acute root desiccation risk. |

---

## 7. Domain Guardrails (`domain_guardrails.py`)

Milestone 8D revealed that the frozen ANFIS model performs exceptionally well on open-field mineral soils ($R^2 = 0.81$ on validation), but extrapolates poorly when presented with extreme soilless desiccation regimes ($clay \le 2.0\%$ and moisture $< 15\%$).

The guardrail module inspects every input **before** the decision layer accepts the ANFIS prediction:

1. **Extreme Soil Moisture Limits:** Rejects $\theta < 1.0\%$ or $\theta > 70.0\%$.
2. **Clay Bounds:** Validates clay is within $[0.0\%, 80.0\%]$.
3. **Environmental Physical Bounds:** Temperature $[-10^\circ\text{C}, 60^\circ\text{C}]$, RH $[0\%, 100\%]$, $\text{ET}_0 [0, 25 \text{ mm/day}]$.
4. **Milestone 8D Soilless Drydown Intercept:**
   If $\text{clay} \le 2.0\%$ AND $(\theta_{current} < 15.0\% \text{ or } \theta_{24h} < 15.0\%)$:
   Triggers `GUARD_MILESTONE_8D_EXTREME_DRYDOWN`, overrides ANFIS, and returns `INSUFFICIENT_CONFIDENCE`.
5. **Crop Profile & MAD Integrity:** If the crop is unrecognized or has unverified MAD parameters, returns `INSUFFICIENT_CONFIDENCE`.

---

## 8. Decision Reliability Classification

Reliability reflects data integrity, domain adherence, and parameter validation:

- **`HIGH`**: All telemetry inputs present and well within training distribution; crop profile fully validated with peer-reviewed FAO-56 parameters; ANFIS operating in prime mineral soil regime.
- **`MEDIUM`**: Inputs within physiological bounds; secondary parameters estimated or growth stage interpolated from DAP fallback.
- **`LOW`**: Missing non-critical context (e.g., planting date unknown, generic default soil texture used).
- **`UNAVAILABLE`**: Guardrails triggered (out-of-domain telemetry, unrecognized crop, or unvalidated MAD threshold).

> [!NOTE]
> Reliability is a deterministic **decision reliability classification**, NOT a statistical Bayesian probability.

---

## 9. Decision States & Farmer Explanations

| Decision | Condition | Human-Readable Explanation Example |
| :--- | :--- | :--- |
| `NO_IRRIGATION` | Moisture `SAFE` or `HIGH` | *"No irrigation is needed right now. Predicted soil moisture for the next 24 hours remains comfortably above the crop's allowable depletion threshold."* |
| `MONITOR` | Moisture within buffer above MAD ($< \text{Threshold}_{MAD} + 0.15 \times \text{RAW}$) | *"Soil moisture is currently sufficient but approaching the allowable depletion threshold. Monitor field conditions over the next 24 hours."* |
| `IRRIGATION_RECOMMENDED` | Moisture `DEFICIT` ($\theta_{24h} < \text{Threshold}_{MAD}$) | *"Irrigation is recommended. Soil moisture is projected to fall below the allowable depletion threshold within 24 hours."* |
| `IRRIGATION_URGENT` | Moisture `SEVERE_DEFICIT` ($\theta_{24h} \le \text{PWP}$) | *"Urgent irrigation required! Soil moisture has reached critical deficit levels near the permanent wilting point, posing imminent danger of crop water stress."* |
| `INSUFFICIENT_CONFIDENCE` | Guardrail violation or unvalidated agronomic parameters | *"The system cannot safely make an irrigation recommendation because inputs are outside the validated operating domain: [Specific Reason]."* |

### Irrigation Method & Water Availability Adjustments
- **Method Retention:** Retains delivery type in recommendation context. Advises high frequency / low volume for Drip, evening scheduling to reduce evaporative drift for Sprinkler, and border containment monitoring for Flood.
- **Water Availability Constraint:** When water availability is `Limited` and irrigation is `RECOMMENDED` or `URGENT`, the warning is **NEVER suppressed**. The engine flags:
  > *"Water availability is limited. Prioritize root-zone application to critical crop stages or apply deficit irrigation tactics to safeguard yields."*

---

## 10. API Specification

### Endpoint: `POST /api/decision/recommendation`

#### Request Body
```json
{
  "assessment": {
    "crop": "Tomato",
    "planting_date": "2026-08-15",
    "farm_size": 2.5,
    "farm_size_unit": "Acres",
    "irrigation_method": "Drip",
    "water_availability": "Moderate"
  },
  "environment": {
    "soil_moisture_root_zone": 28.5,
    "et0_fao_evapotranspiration": 4.8,
    "temperature_2m": 29.4,
    "relative_humidity_2m": 52.0,
    "clay_content": 24.0
  },
  "predicted_target_mean_24h": 22.8
}
```

#### Response Body
```json
{
  "decision": "IRRIGATION_RECOMMENDED",
  "confidence": "HIGH",
  "current_moisture": 28.5,
  "predicted_moisture_24h": 22.8,
  "field_capacity": 31.0,
  "permanent_wilting_point": 15.0,
  "mad_threshold": 24.6,
  "crop": "Tomato",
  "crop_stage": "mid_season",
  "days_after_planting": 52,
  "reason": "Irrigation is recommended. Soil moisture is projected to fall below the crop's allowable depletion threshold within 24 hours. The crop is currently in its water-sensitive mid_season stage (DAP 52).",
  "domain_status": "VALIDATED_DOMAIN",
  "warnings": [],
  "context": {
    "irrigation_method": "Drip",
    "water_availability": "Moderate",
    "farm_size": 2.5,
    "farm_size_unit": "Acres"
  }
}
```

---

## 11. Agronomic Validation Requirements & Audit Trail

All agronomic values in `crop_profiles.json` are tagged with peer-reviewed literature sources:
- **FAO Irrigation and Drainage Paper 56:** Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998). *Crop evapotranspiration - Guidelines for computing crop water requirements*. FAO, Rome.
- **USDA Natural Resources Conservation Service (NRCS):** *National Engineering Handbook, Part 652: Irrigation Guide*.
- **University Extension References:** UC Davis Vegetable Research and Information Center; Oregon State University Blueberry Management Guides.

Any parameter missing an empirical, peer-reviewed reference must be marked:
```json
"mad_source": "REQUIRES AGRONOMIC VALIDATION"
```
When encountered, the Decision Engine automatically raises a guardrail flag and responds with `INSUFFICIENT_CONFIDENCE`.

---

## 12. Limitations & Boundary Guarantees
1. **Timing & Need Only:** The engine prescribes **whether** irrigation is needed and **how urgently**. It does **not** prescribe volumetric water quantities (litres, cubic meters) or duration (hours/minutes).
2. **No Optimal Irrigation Guarantee:** Irrigation decisions reflect physical depletion boundaries and FAO-56 crop coefficient models; localized microclimates, salinity, soil compaction, and drainage anomalies require on-site ground-truthing.
3. **Frozen ANFIS Architecture:** The Decision Engine does not train, fine-tune, or modify the weights or fuzzy parameters of the upstream ANFIS neural network.
