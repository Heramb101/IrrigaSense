# 🌱 IrrigaSense — Live Demonstration Walkthrough & Academic Guide

> **Document ID:** `GUIDE-DEMO-V1-20261010`
> **Target Audience:** Academic Evaluators, Agronomists, Technical Examiners, and Software Reviewers
> **Platform Version:** Milestone 12 Baseline (Certified Release)

---

## 1. Demonstration Aim & Overview

This guide provides a repeatable, step-by-step walkthrough for demonstrating the **IrrigaSense** intelligent irrigation platform.

The demonstration highlights three core technical pillars:
1. **Zero-Hardware Friction:** A 6-question farmer onboarding flow that automatically derives high-resolution weather, $ET_0$, and soil texture telemetry via **Open-Meteo** and **ISRIC SoilGrids**.
2. **Explainable Neuro-Fuzzy Soil Physics:** A frozen **5-Input, 32-Rule First-Order Takagi-Sugeno ANFIS** model predicting continuous 24-hour root-zone volumetric water content (% VWC).
3. **Deterministic Agronomic Decision Logic:** An **FAO-56 Crop-Aware Decision Engine** that evaluates Managed Allowable Depletion (MAD) to deliver actionable, jargon-free irrigation timing recommendations.

---

## 2. Environment Launch & Health Verification

Ensure both backend and frontend servers are running:

### A. Start the FastAPI Backend
Open a terminal in the project directory:
```bash
# Windows
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Linux / macOS
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- **Verify Health Check:**
  ```bash
  curl http://127.0.0.1:8000/health
  ```
  *Expected Output:* `{"status": "healthy"}`

---

### B. Start the Vite React Frontend
Open a second terminal in the project directory:
```bash
cd frontend
npm run dev
```
- Open your browser to: **`http://localhost:5173/`**

---

## 3. Recommended Demonstration Scenario: Commercial Tomato Farm

To showcase the system's full capabilities, use the following standardized agronomic scenario:

| Parameter | Demonstration Input Value | Agronomic Rationale & Technical Context |
| :--- | :--- | :--- |
| **Location (Q1)** | **Baramati North Farmland, Pune District, Maharashtra** (`18.1550° N, 74.5800° E`) | Prime agricultural region in western India with semi-arid climate and mineral clay loam soil. |
| **Current Crop (Q2)** | **Tomato (*Solanum lycopersicum*)** | Solanaceae crop with high water sensitivity ($p = 0.40$ MAD fraction, Field Capacity: $32\%$, PWP: $15\%$). |
| **Planting Date (Q3)** | **45–60 days before today** (e.g. `2026-08-15`) | Places crop into the critical **Crop Development / Vegetative** stage ($K_c = 1.15$). |
| **Farm Size (Q4)** | **2–5 acres** | Representative medium commercial holding. |
| **Irrigation Method (Q5)**| **Drip Irrigation** | High-efficiency micro-emitter delivery system. |
| **Water Availability (Q6)**| **Moderate** | Typical canal/borewell scheduled rotation. |

---

## 4. Step-by-Step Screen Walkthrough

### Screen 1: Welcome & Q1 — Farm Location
- **Visual:** Interactive map picker centered on farmland coordinates with location confirmation card.
- **Presenter Explanation:**
  > *"Notice that we do not ask the farmer for soil moisture sensors, telemetry loggers, or weather stations. By simply confirming the plot coordinates, IrrigaSense automatically queries Open-Meteo for real-time weather and root-zone moisture, and ISRIC SoilGrids for topsoil clay percentage."*
- **Action:** Select location $\rightarrow$ Click **"Confirm Location & Continue"**.

---

### Screen 2: Q2 — Current Crop Selection
- **Visual:** Interactive crop cards (Tomato, Zucchini, Blueberry) with botanical families.
- **Presenter Explanation:**
  > *"Selecting the crop loads scientific FAO-56 biological parameters: root depth (0.30–0.70m for tomato), dynamic crop coefficients ($K_c$), and the Managed Allowable Depletion fraction ($p = 40\%$)."*
- **Action:** Select **Tomato** $\rightarrow$ Click **"Continue"**.

---

### Screen 3: Q3 — Planting Date & Phenology
- **Visual:** Calendar picker.
- **Presenter Explanation:**
  > *"Given the sowing date, the decision engine computes Days After Planting (DAP) and dynamically tracks phenological growth stages: Initial, Crop Development, Mid-Season, and Late-Season. Tomato water demand peaks significantly during mid-season flowering and fruit set."*
- **Action:** Choose planting date $\rightarrow$ Click **"Continue"**.

---

### Screen 4 to 6: Q4 (Farm Size), Q5 (Method), Q6 (Water Availability)
- **Visual:** Radio card selectors for operational context.
- **Presenter Explanation:**
  > *"These parameters provide operational context. Note that in accordance with agronomic safety principles, IrrigaSense maintains volumetric restraint: we advise on timing and urgency, avoiding uncalibrated gallon guesses that could lead to overwatering."*
- **Action:** Select `2–5 acres`, `Drip`, and `Moderate` $\rightarrow$ Advance to Review.

---

### Screen 7: Review & Final Confirmation
- **Visual:** Clean summary review screen displaying all 6 confirmed parameters.
- **Action:** Click **"Confirm & Launch Live Advisory"**.

---

### Screen 8: Live Farmer Dashboard
The dashboard delivers an intuitive, jargon-free precision advisory:

1. **Irrigation Recommendation Hero Banner:**
   - Visual status badge (`NO_IRRIGATION`, `MONITOR`, `IRRIGATION_RECOMMENDED`, `IRRIGATION_URGENT`, or `INSUFFICIENT_CONFIDENCE`).
   - Plain-language explanation (e.g., *"No irrigation is needed right now. Predicted soil moisture for the upcoming 24 hours remains comfortably above the allowable depletion threshold."*).
2. **Root-Zone Soil Moisture Gauges:**
   - **Observed Root-Zone Moisture (% VWC):** Current moisture level from telemetry.
   - **ANFIS 24-Hour Forecast (% VWC):** Neuro-fuzzy projection of moisture 24 hours ahead.
   - **Allowable Depletion Threshold (MAD):** Dynamic crop threshold ($24.8\%$ for tomato).
3. **Crop Phenology & Diagnostics Card:**
   - Displays Days After Planting (DAP), current growth stage (*Crop Development*), and root zone characteristics.
4. **Live Weather Card:**
   - Current air temperature (°C), relative humidity (%), precipitation (mm), and reference evapotranspiration ($ET_0$, mm/day).
5. **Satellite Farmland View:**
   - Overhead optical imagery providing geographical plot context with an explicit disclaimer that satellite tiles do not measure moisture directly.

---

### Screen 9: Demonstrating Reliability & Error Handling
To demonstrate system resilience:
1. Temporarily stop the backend server (`Ctrl+C` in backend terminal) or disconnect network.
2. Click **↻ Refresh** in the dashboard.
3. **Observed Behavior:** The dashboard invalidates previous data and renders a prominent **"Recommendation Temporarily Unavailable"** error state with an **Agronomic Advisory Warning** and a **"↻ Retry Analysis"** action.
4. **Presenter Explanation:**
   > *"Unlike naive systems that silently show outdated or fabricated high-confidence data during outages, IrrigaSense guarantees that an unverified recommendation is never presented as factual advice."*
5. Restart backend $\rightarrow$ Click **"↻ Retry Analysis"** $\rightarrow$ Dashboard cleanly re-evaluates and displays live cards.

---

## 5. Machine Learning & Neuro-Fuzzy Architecture Explanation

When presenting to academic or technical evaluators, reference these core scientific principles:

```
+---------------------------------------------------------------------------------------------------+
|                            FIRST-ORDER TAKAGI-SUGENO ANFIS ARCHITECTURE                           |
|                                                                                                   |
|  Inputs (5): [Soil Moisture, ET0, Temp, RH, Clay Content]                                         |
|      ↓                                                                                            |
|  Layer 1: Premise Gaussian Membership Functions (Low / High per input) → μ_A(x) = exp(-(x-c)²/2σ²) |
|      ↓                                                                                            |
|  Layer 2: Product T-Norm Rule Firing Strengths (32 Rules: 2^5 Grid Partition)                     |
|      ↓                                                                                            |
|  Layer 3: Analytical Log-Sum-Exp Normalized Firing Strengths (w_i_bar)                            |
|      ↓                                                                                            |
|  Layer 4: First-Order Consequent Hyperplanes: f_i(X) = p_i1*x1 + ... + p_i5*x5 + r_i              |
|      ↓                                                                                            |
|  Layer 5: Defuzzified Crisp Soil Moisture Forecast: y = ∑ (w_i_bar * f_i(X))                      |
+---------------------------------------------------------------------------------------------------+
```

### Key Technical Talking Points:
1. **Why Regression?** Soil moisture dynamics follow physical mass-conservation and hydraulic laws. Predicting continuous volumetric water content (% VWC) 24 hours into the future provides physical state projections rather than opaque discrete labels.
2. **Why ANFIS over Other Techniques?**
   - **vs. Discrete Classifiers (Naive Bayes / Random Forest Classifier):** Discrete labels fail to adapt when soil texture or crop stage shifts the critical threshold.
   - **vs. Black-Box Neural Networks (MLP / LSTM):** ANFIS provides full transparency: every rule has explicit linguistic premise centers ($c, \sigma$) and first-order linear gradients ($p_{ij}, r_i$).
   - **vs. Reinforcement Learning (Q-Learning):** Q-learning requires an interactive environment or simulator; ANFIS directly models the nonlinear physical moisture drydown curve from empirical data.
3. **Decoupling Prediction from Decision:**
   - **ANFIS Predicts Physics:** Computes $\hat{\theta}_{24h}$ (physical soil moisture).
   - **Decision Engine Evaluates Biology:** Evaluates whether $\hat{\theta}_{24h} < \text{Threshold}_{MAD}$ for the specific crop at its current DAP.
4. **Transparent Out-of-Sample Performance Breakdown:**
   - **Validation Split (15% chronological, 7,051 rows):** $R^2 \approx 0.770$, $\text{MAE} \approx 5.66\%$ VWC ($R^2 \approx 0.81$ on mineral zones).
   - **Open-Field Mineral Soil Test Cohort (Zones 2 & 4, 68.6% of test set):** $R^2 = 0.985$, $\text{MAE} = 1.96\%$ VWC, $\text{RMSE} = 2.62\%$ VWC.
   - **Aggregate Held-Out Test Set (7,051 rows):** $R^2 = -0.475$, $\text{MAE} = 17.28\%$ VWC. Potted blueberry in Zone 5 underwent post-harvest terminal drydown to $3.71\%$ VWC (unobserved during training where Zone 5 was saturated at $69.7\%$).
   - **Production Guardrail:** Demonstrates scientific integrity—rather than papering over the soilless desiccation limitation, `GUARD_MILESTONE_8D_EXTREME_DRYDOWN` intercepts unvalidated soilless drydowns and safely returns `INSUFFICIENT_CONFIDENCE`.

---

## 6. Verification Methods Matrix

| Step / Feature | Verification Method | Verification Evidence |
| :--- | :--- | :--- |
| **1. Service Startup & Health** | API HTTP Check | `GET /health` returned `200 OK` (`{"status": "healthy"}`). |
| **2. 6-Question Assessment Flow** | Automated Test Suite | `frontend/src/tests/flow.test.ts` (12/12 passed). |
| **3. Upstream Telemetry Resolution** | Live Backend HTTP Request | Auto-resolved Open-Meteo ($26.9^\circ\text{C}, ET_0 = 5.34\text{ mm}$) and SoilGrids ($22.6\%$ clay). |
| **4. Frozen ANFIS Forward Pass** | Live API + Integration Tests | `tests/test_anfis_decision_integration.py` (5/5 passed); generated $\hat{\theta}_{24h} = 27.84\%$ VWC. |
| **5. Decision Engine Evaluation** | Automated Test Suite | `tests/test_decision_engine.py` (16/16 passed). |
| **6. Dashboard Card Rendering** | Automated Test Suite | `frontend/src/tests/dashboard.test.ts` (23/23 passed). |
| **7. Error Resilience & Retry** | Automated Regression Suite | Simulated fetch failure, 500 server error, and retry transitions (Tests 16–20 passed). |
| **8. Interactive Browser Walkthrough**| Manual User Browser | Verified in user browser at `http://localhost:5173/` *(Headless Playwright automated runner encountered upstream CDN 404)*. |

---

## 7. Troubleshooting & Demonstration FAQs

- **Q: What if Open-Meteo or SoilGrids is slow during the live demo?**
  *A:* The backend decision route enforces an automatic timeout fallback: if SoilGrids is unreachable, it applies regional baseline topsoil clay ($22.6\%$) and flags the warning in response diagnostics.
- **Q: What if the Google Maps API key is expired or restricted?**
  *A:* The frontend includes a built-in Non-API Developer Fallback with interactive coordinate presets, ensuring the questionnaire never crashes or stalls.
- **Q: Why does the moisture forecast change slightly from day to day?**
  *A:* Open-Meteo weather parameters ($ET_0$, temperature, humidity, wind) reflect real-time meteorological conditions at the farm coordinates, which dynamically drive the ANFIS premise activations and consequent calculations.
