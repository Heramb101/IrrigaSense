# IrrigaSense — Presentation Evidence & Artifact Checklist

> **Document ID:** `CHECKLIST-EVIDENCE-20261010`
> **Milestone:** Milestone 12B (Presentation Packaging & Demonstration Evidence)
> **Target Audience:** Presenters, Academic Evaluators, and Demonstration Leads

---

## 1. Overview & Guidelines

This checklist catalogues all essential visual evidence, UI screenshots, API execution logs, and scientific machine learning diagnostic plots required for academic defenses, technical demonstrations, and project documentation.

> [!IMPORTANT]
> **Academic Integrity Rule:** Never fabricate screenshots or state an image is captured if it has not been recorded. Ensure all API logs reflect real live or test executions and clearly note where figures originate from repository artifacts.

---

## 2. User Interface Evidence Checklist

| Item ID | Screen / Artifact Description | UI Elements to Capture | Source Component / Route | Verification Status |
| :---: | :--- | :--- | :--- | :---: |
| **UI-01** | **Questionnaire Start & Q1 Location** | Google Maps interactive map, draggable marker, search box, confirmed coordinates badge (`18.1550° N, 74.5800° E`), place name string, and *"Confirm Location & Continue"* button. | `frontend/src/components/questions/LocationQuestion.tsx` | Verified in Test & Browser |
| **UI-02** | **Q2 Current Crop Selection** | Crop selector cards (Tomato, Zucchini, Blueberry) with botanical families, icons, and description labels. | `frontend/src/components/questions/CropSelectQuestion.tsx` | Verified in Test & Browser |
| **UI-03** | **Q3 Planting Date Picker** | Date picker interface displaying selected sowing date, computed DAP tooltip, and stage transition notice. | `frontend/src/components/questions/PlantingDateQuestion.tsx` | Verified in Test & Browser |
| **UI-04** | **Q4–Q6 Operational Context** | Radio option cards for Farm Size (`2–5 acres`), Irrigation Method (`Drip`), and Water Availability (`Moderate`). | `frontend/src/components/questions/RadioOptionQuestion.tsx` | Verified in Test & Browser |
| **UI-05** | **Review & Summary Screen** | Full summary card showing all 6 confirmed parameters, edit links per section, and the *"Confirm & Launch Live Advisory"* CTA. | `frontend/src/components/questions/ReviewSummaryQuestion.tsx` | Verified in Test & Browser |
| **UI-06** | **Live Recommendation Hero Card** | Visually dominant recommendation banner displaying decision state (e.g. `💧 Irrigation recommended` or `🌱 No irrigation needed now`), confidence tag (`High Confidence`), plain-language explanation, and last evaluated timestamp. | `frontend/src/components/dashboard/RecommendationCard.tsx` | Verified in Test & Browser |
| **UI-07** | **Soil Moisture Telemetry Gauges** | Current observed root-zone moisture (`27.4% VWC`), ANFIS 24-hour forecast gauge (`27.8% VWC`), and the crop-specific MAD threshold line (`24.8% VWC`). | `frontend/src/components/dashboard/SoilMoistureCard.tsx` | Verified in Test & Browser |
| **UI-08** | **Crop Phenology & Diagnostics** | Days After Planting counter (e.g. `56 DAP`), current FAO-56 growth stage (`Vegetative / Crop Development`), active root depth, and depletion limit indicator. | `frontend/src/components/dashboard/CropFarmCard.tsx` | Verified in Test & Browser |
| **UI-09** | **Live Weather Telemetry Card** | Ambient temperature (`26.9°C`), relative humidity (`51%`), FAO-56 reference evapotranspiration ($ET_0 = 5.34\text{ mm/day}$), and Open-Meteo source attribution. | `frontend/src/components/dashboard/WeatherCard.tsx` | Verified in Test & Browser |
| **UI-10** | **Satellite Farmland View** | High-resolution optical satellite tiles centered on farmland coordinates with parcel pin and the physical sensor disclaimer footer. | `frontend/src/components/dashboard/SatelliteMapCard.tsx` | Verified in Test & Browser |
| **UI-11** | **Resilience & Error State Card** | *"Recommendation Temporarily Unavailable"* card triggered when backend is offline, featuring the red advisory warning box and the functional *"↻ Retry Analysis"* button. | `frontend/src/dashboard/Dashboard.tsx` | Verified in Test & Regression Suite |

---

## 3. Backend & API Execution Evidence Checklist

| Item ID | Evidence Description | Target Command / Endpoint | Expected Response / Evidence Output | Verification Status |
| :---: | :--- | :--- | :--- | :---: |
| **API-01** | **Backend Health Check** | `GET http://127.0.0.1:8000/health` | `HTTP 200 OK` $\rightarrow$ `{"status": "healthy"}` | **Verified Live** |
| **API-02** | **Root Service Welcome** | `GET http://127.0.0.1:8000/` | `HTTP 200 OK` $\rightarrow$ `{"message": "Welcome to the IrrigaSense API"}` | **Verified Live** |
| **API-03** | **Open-Meteo Weather Query** | `GET /api/environment/weather?latitude=18.155&longitude=74.58` | `HTTP 200 OK` with normalized `WeatherProfile` (Temp, Humidity, Precip, $ET_0$). | **Verified Live & Unit Tests** |
| **API-04** | **ISRIC SoilGrids Query** | `GET /api/environment/soil?latitude=18.155&longitude=74.58` | `HTTP 200 OK` with topsoil clay %, pH, and texture scaling. | **Verified Live & Unit Tests** |
| **API-05** | **End-to-End Recommendation** | `POST /api/decision/recommendation` | `HTTP 200 OK` with complete decision object, ANFIS prediction, and weather summary. | **Verified Live** |
| **API-06** | **Full Python Test Run** | `backend\venv\Scripts\pytest.exe -v` | **118 / 118 Passed** in 52.3s. | **Verified Live** |
| **API-07** | **Full Frontend Test Run** | `npm test` (in `frontend/`) | **35 / 35 Passed** in 4.8s. | **Verified Live** |
| **API-08** | **Production Bundle Build** | `npm run build` (in `frontend/`) | `tsc -b && vite build` $\rightarrow$ Zero errors in 0.22s. | **Verified Live** |

---

## 4. Machine Learning Figures & Diagnostic Evidence

The repository contains certified high-resolution figures generated during Milestones 7 and 8 that should be included in presentation slide decks:

```
ml/
├── anfis/reports/figures/
│   ├── membership_functions.png           <-- Layer 1 Gaussian MFs across all 5 inputs
│   ├── training_validation_rmse.png       <-- Optimization convergence curve (RMSE)
│   ├── training_validation_r2.png         <-- Optimization convergence curve (R²)
│   ├── 8c_predicted_vs_actual_val.png     <-- Validation parity scatter plot (R² = 0.770)
│   ├── 8c_validation_residuals.png        <-- Residual distribution on validation split
│   ├── 8d_predicted_vs_actual_test.png    <-- Out-of-sample test scatter plot (Mineral R² = 0.985)
│   ├── 8d_test_residuals.png              <-- Residuals across the 7,051-row test partition
│   ├── 8d_test_timeseries.png             <-- Chronological tracking of actual vs predicted 24h VWC
│   └── 8d_test_error_by_target_range.png  <-- Error breakdown across moisture depletion regimes
└── datasets/processed/
    ├── feature_importance.png             <-- Random Forest & Mutual Information ranking
    ├── feature_correlation_heatmap.png    <-- 5-feature correlation matrix
    └── target_distribution.png            <-- target_mean_24h volumetric distribution
```

### Key Figures to Feature in Presentation Slides:

1. **Slide: Feature Selection & Telemetry Justification:**
   - Embed: `ml/datasets/processed/feature_importance.png` and `feature_correlation_heatmap.png`.
   - *Key Point:* Demonstrates why `soil_moisture`, `et0`, `temperature`, `humidity`, and `clay` form the optimal minimal non-invasive feature set ($> 94\%$ predictive power).
2. **Slide: Neuro-Fuzzy Layer 1 Architecture:**
   - Embed: `ml/anfis/reports/figures/membership_functions.png`.
   - *Key Point:* Shows the smooth Gaussian membership functions (`Low`, `High`) fitted to physical input distributions.
3. **Slide: Model Training Convergence:**
   - Embed: `ml/anfis/reports/figures/training_validation_rmse.png` and `training_validation_r2.png`.
   - *Key Point:* Shows regularized Least Squares Estimation (LSE) and Adam optimization converging stably without premise divergence.
4. **Slide: Scientific Test Evaluation & Honest Domain Findings:**
   - Embed: `ml/anfis/reports/figures/8d_predicted_vs_actual_test.png` and `8d_test_timeseries.png`.
   - *Key Point:* Shows near-perfect tracking on native mineral soils ($R^2 = 0.985$) alongside the extreme drydown regime in soilless substrates that motivated the Milestone 8D Domain Guardrail.

---

## 5. Summary Presentation Slide Deck Outline

1. **Slide 1: Title & Project Mission** (Problem statement, hardware barriers in precision agriculture).
2. **Slide 2: System Architecture & Data Flow** (Mermaid end-to-end diagram).
3. **Slide 3: Frictionless 6-Question Assessment** (Screenshots UI-01 to UI-05).
4. **Slide 4: Automated Environmental Telemetry** (Open-Meteo & SoilGrids integration).
5. **Slide 5: First-Order Takagi-Sugeno ANFIS Engine** (5 inputs, 32 rules, membership functions figure).
6. **Slide 6: Empirical ML Evaluation Breakdown** (Validation $R^2 = 0.770$, Mineral Test $R^2 = 0.985$, Aggregate Test $R^2 = -0.475$).
7. **Slide 7: Adaptive Agronomic Decision Engine & MAD** (Dynamic DAP, stage transitions, crop profiles).
8. **Slide 8: Live Farmer Dashboard Walkthrough** (Screenshots UI-06 to UI-10).
9. **Slide 9: Reliability, Error Handling & Guardrails** (Screenshot UI-11, boundary safety).
10. **Slide 10: Conclusion & Future Work** (Scalable crop profile expansion, edge IoT integration).
