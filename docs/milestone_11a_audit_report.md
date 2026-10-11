# IrrigaSense — Milestone 11A: Repository Audit & Release Validation Report

> **Document ID:** `DOC-M11A-AUDIT-20261010`
> **Milestone:** Milestone 11A (End-to-End Validation, Reliability & Release Readiness)
> **Audit Date:** 2026-10-10
> **Auditor:** Automated Agentic Pair-Programming System (DeepMind Antigravity)
> **Branch & Commit Baseline:** `main` (commit `0c90610`)
> **Target Status:** Baseline Established for Milestone 11B Remediation

---

## 1. Executive Summary

Milestone 11 initiates the final release validation, end-to-end reliability assessment, and hardening phase of the **IrrigaSense** precision irrigation platform. This audit establishes a rigorous, empirical baseline across all subsystems:
1. **6-Question Farmer Onboarding Flow** (Google Maps pinpointing, crop selection, DAP computation, operational context),
2. **Automated Environmental & Soil Telemetry Resolvers** (Open-Meteo Weather API & ISRIC SoilGrids REST/WCS),
3. **Frozen 5-Input / 32-Rule First-Order Takagi-Sugeno ANFIS Engine** (`anfis_final_validation_best.json`),
4. **Deterministic Agronomic Decision Engine & Domain Guardrails** (FAO-56 phenological profiles & MAD evaluation),
5. **React Farmer Dashboard** (Visual recommendation badges, soil moisture gauges, live weather, satellite imagery).

### Key Audit Findings:
- **Test Baseline:** **145 total automated tests** (118 Python pytest + 27 TypeScript frontend tests) currently execute with a **100% pass rate** (0 failures, 0 errors).
- **Model & Dataset Integrity:** SHA-256 hashes of the frozen ANFIS model (`9bd06f09...`) and master training dataset (`fe11346d...`) match certified release values bit-for-bit. Quarantined test partitions remain untouched.
- **Critical Defect Identified:** In `frontend/src/dashboard/Dashboard.tsx`, failure of the backend decision API silently catches exceptions and defaults to a hardcoded mock payload with `decision: 'NO_IRRIGATION'` and `confidence: 'HIGH'`, violating safety invariants during backend outages.
- **Documentation Gaps:** `README.md` is practically empty (35 bytes); `docs/assessment_specification.md` documents a legacy 20-question specification rather than the active 6-question workflow.
- **Security Finding:** `frontend/.env.example` contains an active Google Maps API key rather than an empty placeholder.

---

## 2. Repository & Branch Status

- **Active Branch:** `main` (tracking `origin/main` at `https://github.com/Heramb101/IrrigaSense.git`)
- **Latest Commit:** `0c90610` (*"fix: integrate ANFIS prediction with decision engine"*)
- **Working Tree State:**
  - `frontend/.env.example` (unstaged modification: active API key inserted)
  - `ml/datasets/processed/dataset_validation_report.md` (unstaged modification: timestamp updated during test execution)
  - `ml/datasets/processed/feature_selection_report.md` (unstaged modification: timestamp updated during test execution)
- **Zero Untracked / Stray Critical Files:** Working tree is clean and aligned with release structure.

---

## 3. Actual Architecture & Entry Points

```
+---------------------------------------------------------------------------------------------------+
|                                          USER INTERFACE                                           |
|  React 19 + TypeScript + Vite                                                                     |
|  Entry: frontend/src/main.tsx -> frontend/src/App.tsx                                             |
|  Flow: AssessmentLayout -> QuestionDispatcher (Q1..Q6, REVIEW) -> Dashboard                       |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v  HTTP POST /api/decision/recommendation
+---------------------------------------------------------------------------------------------------+
|                                      BACKEND API ROUTER                                           |
|  FastAPI + Uvicorn + SQLAlchemy (SQLite: irrigasense.db)                                          |
|  Entry: backend/app/main.py -> backend/app/routes/decision.py                                     |
+---------------------------------------------------------------------------------------------------+
                                                  |
                +---------------------------------+---------------------------------+
                |                                                                   |
                v                                                                   v
+-----------------------------------------------+   +-----------------------------------------------+
|             TELEMETRY SERVICES                |   |             ANFIS INFERENCE SERVICE           |
|  1. Open-Meteo (open_meteo.py)                |   |  backend/app/services/decision_engine/        |
|     - ET0, Temp, RH, Precipitation            |   |    anfis_inference.py                         |
|     - Root-zone soil moisture (7-28cm)        |   |  - Loads: anfis_final_validation_best.json    |
|  2. ISRIC SoilGrids (soilgrids.py)            |   |  - Normalization: normalization.json          |
|     - Topsoil clay %, texture, pH             |   |  - Output: predicted_target_mean_24h          |
+-----------------------------------------------+   +-----------------------------------------------+
                |                                                                   |
                +---------------------------------+---------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                              ADAPTIVE AGRONOMIC DECISION ENGINE                                   |
|  backend/app/services/decision_engine/decision_engine.py                                          |
|  1. Domain Guardrails (domain_guardrails.py): Boundary and data sanity validation                 |
|  2. Crop Profile Manager (crop_profiles.py): FAO-56 stage & MAD calculation                       |
|  3. Moisture State Evaluator (moisture_state.py): Compares forecast against MAD threshold         |
+---------------------------------------------------------------------------------------------------+
```

### Primary Subsystem Entry Points:
| Subsystem | File Path | Purpose |
| :--- | :--- | :--- |
| **Backend Main Application** | `backend/app/main.py` | FastAPI application factory, CORS setup, router mounting (`/api/assessments`, `/api/environment`, `/api/decision`). |
| **Decision Recommendation Route** | `backend/app/routes/decision.py` | Primary API aggregating farm coordinates, telemetry, ANFIS forecast, and agronomic decisions. |
| **Environmental Telemetry Route** | `backend/app/routes/environment.py` | Standalone query endpoints for Open-Meteo weather and ISRIC SoilGrids soil profiles. |
| **Assessment Route** | `backend/app/routes/assessments.py` | Assessment persistence and CRUD endpoints against SQLite database (`irrigasense.db`). |
| **ANFIS Inference Service** | `backend/app/services/decision_engine/anfis_inference.py` | Singleton forward-pass inference runner executing the frozen 32-rule neural-fuzzy model. |
| **Agronomic Decision Engine** | `backend/app/services/decision_engine/decision_engine.py` | Deterministic rule orchestrator computing MAD depletion, DAP, phenological stage, and decision states. |
| **Domain Guardrails** | `backend/app/services/decision_engine/domain_guardrails.py` | Safety boundary enforcer preventing unvalidated extrapolation (e.g. Milestone 8D extreme drydown). |
| **Frontend Application** | `frontend/src/App.tsx` | Context provider and top-level layout container. |
| **Assessment Dispatcher** | `frontend/src/components/questions/QuestionDispatcher.tsx` | Routes active questions Q1–Q6 and renders Review/Dashboard on completion. |
| **Farmer Dashboard** | `frontend/src/dashboard/Dashboard.tsx` | Farmer advisory presentation layer including recommendation card, telemetry gauges, and satellite view. |

---

## 4. Test Execution & Verification Results

All automated test suites were executed in a clean read-only audit run without modifying existing code.

### A. Python Test Suite (pytest)
- **Command:** `backend\venv\Scripts\pytest.exe -v`
- **Execution Time:** 51.22 seconds
- **Exit Code:** `0`
- **Total Tests Collected:** 118
- **Passed:** 118 (100%)
- **Failed:** 0
- **Errors:** 0

#### Detailed Python Test Breakdown:
| Test Module | Suite Description | Tests Passed | Status |
| :--- | :--- | :---: | :---: |
| `backend/tests/test_api.py` | Assessment REST API endpoints, CRUD & HTTP error handling | 7 / 7 | PASS |
| `backend/tests/test_assessment.py` | Assessment schema validation & soil precedence rules | 5 / 5 | PASS |
| `backend/tests/test_environment.py` | Open-Meteo weather service normalization, timeouts, errors | 19 / 19 | PASS |
| `backend/tests/test_soilgrids.py` | ISRIC SoilGrids coordinate transform, scaling, WCS errors | 20 / 20 | PASS |
| `tests/test_anfis_decision_integration.py` | End-to-end integration: Telemetry $\rightarrow$ ANFIS $\rightarrow$ Decision API | 5 / 5 | PASS |
| `tests/test_decision_engine.py` | Milestone 9 Decision Engine: MAD rules, DAP, crop stages, guardrails | 16 / 16 | PASS |
| `tests/test_milestone_7a_dataset.py` | Dataset cleaning, 5 zones, target computation, zero leakage | 11 / 11 | PASS |
| `tests/test_milestone_7b_features.py` | Feature importance, mutual information, 5-input selection | 9 / 9 | PASS |
| `tests/test_milestone_8b_anfis.py` | ANFIS Architecture A/B baselines, forward inference, checkpoints | 9 / 9 | PASS |
| `tests/test_milestone_8c_anfis.py` | ANFIS optimization, validation evaluation, parameter shapes | 10 / 10 | PASS |
| `tests/test_milestone_8d_anfis.py` | Quarantined test evaluation integrity, frozen model verification | 9 / 9 | PASS |
| **Total Python Test Count** | | **118 / 118** | **100% PASS** |

### B. Frontend TypeScript Test Suite
- **Command:** `cmd /c npm test` (in `frontend/`)
- **Execution Time:** 4.5 seconds
- **Exit Code:** `0`
- **Total Tests Collected:** 27
- **Passed:** 27 (100%)
- **Failed:** 0

#### Detailed Frontend Test Breakdown:
| Test File | Scope | Tests Passed | Status |
| :--- | :--- | :---: | :---: |
| `frontend/src/tests/flow.test.ts` | Milestone 6A: Google Maps picker, coordinates update, confirmation gate, Q1–Q6 traversal | 12 / 12 | PASS |
| `frontend/src/tests/dashboard.test.ts` | Milestone 10: Farmer dashboard rendering, 5 decision states, moisture gauges, ML abstraction, volumetric restraint | 15 / 15 | PASS |
| **Total Frontend Test Count** | | **27 / 27** | **100% PASS** |

### Grand Test Suite Total: **145 / 145 Tests Passing (100%)**

---

## 5. Frozen Model & Dataset Integrity Verification

Strict compliance verification was performed programmatically without modifying weights or evaluating the quarantined test partition:

| Artifact | File Path | Expected SHA-256 | Actual Verified SHA-256 | Integrity Status |
| :--- | :--- | :--- | :--- | :---: |
| **Frozen ANFIS Model** | `ml/anfis/artifacts/anfis_final_validation_best.json` | `9bd06f090405ad8ba8f89a4a19c9c38ccb717bec7f12d979934ca92e7c9fc2f7` | `9bd06f090405ad8ba8f89a4a19c9c38ccb717bec7f12d979934ca92e7c9fc2f7` | **CERTIFIED UNCHANGED** |
| **Master Training Dataset** | `ml/datasets/processed/irrigation_anfis_dataset.csv` | `fe11346d873d65598ff37eeac2196da497c3ab82299b0f9f6be1356fd299b2c8` | `fe11346d873d65598ff37eeac2196da497c3ab82299b0f9f6be1356fd299b2c8` | **CERTIFIED UNCHANGED** |
| **Normalization Table** | `ml/anfis/artifacts/normalization.json` | Fitted on Train split (32,905 rows) | Verified strictly train partition bounds | **CERTIFIED VALID** |

---

## 6. Discrepancies Between Documentation and Reality

1. **Conflicting Test Count Reporting:**
   - Prior summaries reported test counts of "67 passed" (referencing only root `tests/`) or "51 passed" (referencing only `backend/tests/`).
   - **Audit Reality:** The repository contains **118 Python tests** across both test directories, plus **27 TypeScript tests**, for a true total of **145 automated tests**.

2. **ANFIS Metric Inconsistencies across Reports:**
   - *Validation Phase (`8C_optimization_results.md`):* Validation $R^2 = 0.7701$ across all validation rows; mineral soil zones reached $R^2 \approx 0.811$.
   - *Final Test Phase (`8D_final_test_evaluation.md`):*
     - Aggregate Raw Test Set (all 7,051 out-of-sample rows): $\text{MAE} = 17.2831\%$ VWC, $\text{RMSE} = 28.6902\%$ VWC, $R^2 = -0.4753$.
     - Open-Field Agricultural Mineral Soil Cohort (68.6% of test set): $\text{MAE} = 1.9595\%$ VWC, $\text{RMSE} = 2.6190\%$ VWC, $R^2 = 0.9850$.
     - Soilless Organic Potted Substrate Cohort (31.4% of test set): $\text{MAE} = 50.7171\%$ VWC (harvest terminal drydown out-of-distribution finding).
   - **Audit Reality:** Broad claims such as *"ANFIS achieves $R^2 = 0.81$ on test data"* in informal summaries conflate validation and test metrics. The true out-of-sample test behavior is strongly bi-modal: near-perfect on mineral soils ($R^2 = 0.985$), but failing on extreme soilless desiccation—which is safely intercepted by the Milestone 8D guardrail.

3. **Outdated Assessment Specification (`docs/assessment_specification.md`):**
   - Documents an obsolete 20-question questionnaire requiring manual inputs for soil tests, weather confirmation, and farm history.
   - **Audit Reality:** The production application operates on a frictionless 6-question workflow (Q1: Location, Q2: Crop, Q3: Planting Date, Q4: Farm Size, Q5: Method, Q6: Water Availability) with automated environmental telemetry.

4. **Empty Root `README.md`:**
   - Contains only 3 lines and 35 bytes without project overview, architecture, quickstart instructions, or API documentation.

---

## 7. Verified Defects, Risks, and Missing Coverage

### A. Verified Defects (Immediate Fix Required in M11B)

1. **DEF-01: Silent Confident Fallback in Frontend Dashboard on Backend Error [CRITICAL]**
   - **Location:** `frontend/src/dashboard/Dashboard.tsx` (lines 63–98)
   - **Behavior:** When the backend `/api/decision/recommendation` endpoint fails (e.g. backend offline, network failure, or HTTP 500), the catch block catches the error and sets a hardcoded mock payload:
     `{ decision: 'NO_IRRIGATION', confidence: 'HIGH', current_moisture: 26.5, ... }`.
   - **Impact:** An offline backend or connection timeout gives the farmer a completely fabricated, confident "NO_IRRIGATION" advice instead of alerting the farmer or displaying an `INSUFFICIENT_CONFIDENCE` state with `confidence: 'UNAVAILABLE'`.
   - **Severity:** **HIGH / BLOCKER**

2. **DEF-02: Hardcoded Sensitive API Key in `frontend/.env.example` [MEDIUM]**
   - **Location:** `frontend/.env.example` (line 4)
   - **Behavior:** Contains a live Google Maps API key `AIzaSy...` rather than an empty placeholder `VITE_GOOGLE_MAPS_API_KEY=`.
   - **Severity:** **MEDIUM**

3. **DEF-03: Missing Backend `.env.example` [LOW]**
   - **Location:** `backend/`
   - **Behavior:** No template file exists to document backend environment configurations (e.g., `DATABASE_URL`, `PORT`, `CORS_ORIGINS`).
   - **Severity:** **LOW**

### B. Potential Risks & Technical Debt

1. **RISK-01: Static Mineral Soil Fallback for Missing Soil Data**
   - **Location:** `backend/app/routes/decision.py` (lines 146, 153)
   - **Detail:** If SoilGrids cannot resolve clay content, clay defaults to `22.6%` (standard mineral soil). If a user enters an unlisted potted substrate, this fallback could prevent the soilless guardrail from triggering.
   - **Mitigation:** Ensure fallback is explicitly flagged in response `warnings`.

2. **RISK-02: Orphaned Legacy Question Components in Frontend**
   - **Location:** `frontend/src/components/questions/`
   - **Detail:** Components like `SoilReportQuestion.tsx`, `WeatherQuestion.tsx`, and `CropStageQuestion.tsx` are unmounted legacy artifacts from the 20-question prototype that import `mockData.ts`.
   - **Mitigation:** Safely prune or archive legacy components in M11B.

3. **RISK-03: Starlette Deprecation Warning during Test Runs**
   - **Location:** `fastapi.testclient` import
   - **Detail:** `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`
   - **Mitigation:** Addressed in requirements update when modernizing dependencies.

---

## 8. Prioritized Remediation Plan for Milestone 11B

| Priority | Task ID | Remediation Action | Affected Files | Target Milestone |
| :---: | :---: | :--- | :--- | :---: |
| **P0** | `FIX-01` | Replace silent confident fallback in `Dashboard.tsx` with honest `INSUFFICIENT_CONFIDENCE` error UI | `frontend/src/dashboard/Dashboard.tsx`, `frontend/src/components/dashboard/RecommendationCard.tsx` | Milestone 11B |
| **P1** | `FIX-02` | Sanitize `frontend/.env.example` and create `backend/.env.example` | `frontend/.env.example`, `backend/.env.example` | Milestone 11B |
| **P1** | `DOC-01` | Update `README.md` with comprehensive architecture, quickstart, and testing guide | `README.md` | Milestone 11B |
| **P2** | `DOC-02` | Update `docs/assessment_specification.md` to reflect the active 6-question workflow | `docs/assessment_specification.md` | Milestone 11B |
| **P2** | `CLN-01` | Clean up dead/orphaned question components and remove redundant mock data linkages | `frontend/src/components/questions/`, `frontend/src/services/mockData.ts` | Milestone 11B |
| **P3** | `TST-01` | Add frontend test explicitly validating error handling when backend returns HTTP 500 / network failure | `frontend/src/tests/dashboard.test.ts` | Milestone 11B |

---

## 9. Conclusion & Milestone 11A Gate Status

- **Integrity Baseline:** **ESTABLISHED & CERTIFIED**
- **Existing Test Suite:** **145/145 PASSING**
- **Model / Data Immutability:** **VERIFIED**
- **Milestone 11A Status:** **COMPLETE** — Ready for targeted reliability fixes in **Milestone 11B**.
