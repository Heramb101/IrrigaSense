# IrrigaSense — Adaptive Neuro-Fuzzy Inference System (ANFIS) Module

> **Milestone 8A Specification & Design Architecture**  
> **Topic:** Adaptive Irrigation Prediction Using Fuzzy Logic and Neural Networks  
> **Algorithm:** First-Order Takagi-Sugeno ANFIS  
> **Input Dimension:** 5 Continuous Physical Variables  
> **Output Dimension:** 1 Continuous Regression Target (`predicted_target_mean_24h`, % VWC)  
> **Current Status:** Architecture Design Frozen. (Zero model training performed in Milestone 8A).

---

## 1. Overview & Module Purpose

The `ml/anfis/` directory contains the mathematical and algorithmic architecture specifications for IrrigaSense's core AI decision engine: a **First-Order Takagi-Sugeno Adaptive Neuro-Fuzzy Inference System (ANFIS)**.

ANFIS combines the qualitative, rule-based interpretability of fuzzy logic systems with the data-driven optimization and non-linear learning power of artificial neural networks. In IrrigaSense, ANFIS predicts the 24-hour mean root-zone volumetric soil moisture ($\hat{y} \in [0, 100]\%$ VWC), enabling precise irrigation advisories that balance crop water requirements with minimal water consumption.

---

## 2. Directory Structure

```
ml/anfis/
├── README.md                 # Module overview, architecture guide, and design governance
├── architecture_spec.md      # Comprehensive 16-section mathematical & algorithmic specification
└── architecture_schema.json  # Machine-readable JSON contract defining inputs, layers, and rules
```

---

## 3. Core Architecture Highlights

- **Frozen 5-Input Feature Vector:**
  1. `soil_moisture_root_zone` (Open-Meteo, 7–28 cm layer, % VWC)
  2. `et0_fao_evapotranspiration` (Open-Meteo, daily FAO-56 Reference ET₀, mm/day)
  3. `temperature_2m` (Open-Meteo, 2m air temperature, °C)
  4. `relative_humidity_2m` (Open-Meteo, 2m relative humidity, %)
  5. `clay_content` (ISRIC SoilGrids, 0–5 cm layer, %)
- **Continuous Regression Target:**
  `target_mean_24h` (Average volumetric soil moisture over upcoming 24 hours, % VWC).
- **Inference Engine:**
  Standard five-layer first-order Sugeno ANFIS with Gaussian membership functions and product T-norm rule firing.
- **Dual Architecture Specification:**
  - **Architecture A (Baseline):** 2 MFs/input $\rightarrow$ **32 rules** $\rightarrow$ **212 trainable parameters** ($20\text{ premise} + 192\text{ consequent}$).
  - **Architecture B (High-Capacity):** 3 MFs/input $\rightarrow$ **243 rules** $\rightarrow$ **1,488 trainable parameters** ($30\text{ premise} + 1,458\text{ consequent}$).
- **Separation of Concerns:**
  Categorical farmer inputs (`crop`, `planting_date`, `farm_size`, `irrigation_method`, `water_availability`) are strictly decoupled from ANFIS. They operate in the post-ANFIS recommendation layer, scaling net depth deficits into actionable volumetric schedules.

---

## 4. Milestone Roadmap & Governance

| Milestone | Scope & Deliverable | Status |
|:---:|:---|:---:|
| **7A** | Dataset cleaning, sensor anomaly filtering, zero leakage confirmation | **COMPLETE** |
| **7B** | Feature analysis, correlation, redundancy pruning, RF baseline | **COMPLETE** |
| **7C** | Production feature availability & data bridge audit | **COMPLETE** |
| **7D** | Open-Meteo soil moisture POC & controlled feature ablation | **PASS** |
| **7E** | Final production feature set & data contract definition | **COMPLETE** |
| **8A** | **ANFIS Architecture Design Only** (No training, parity audit, schema) | **CURRENT** |
| **8B** | Dataset Training Parity Resolution & ANFIS Model Training (Hybrid LSE/GD) | *Upcoming* |
| **8C** | Out-of-Sample Chronological Validation & Benchmark vs RF/Baseline | *Upcoming* |
