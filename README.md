# NexusIQ 🍃
### AI-Powered Energy Management & Optimization Platform
**Predict. Optimize. Sustain.**

> **Competition:** Ideathon 2026 (National Level)  
> **Domain:** Sustainable Energy Management  
> **College:** New Horizon College of Engineering (NHCE)  
> **Team Name:** EcoNexus  

---

## 📌 Problem Statement

Large buildings and campuses (such as universities, corporate offices, hospitals, and commercial complexes) increasingly depend on electricity and renewable sources like rooftop solar. However:
1. **Solar generation is highly variable** throughout the day and weather-dependent.
2. **Electricity consumption fluctuates** sharply with occupancy schedules, equipment usage, and ambient weather.
3. **Absence of coordinated optimization** leads to clean solar power being curtailed or wasted while facilities draw high-tariff electricity from the grid during evening peak hours.
4. **Different facilities have disparate infrastructure**: many older buildings only have utility bills or simple interval meter CSVs, lacking smart batteries or IoT hardware.

**Core Challenge:** *How can we intelligently coordinate energy generation, storage, flexible consumption, and grid interaction into a universal, responsive, and constraint-aware energy ecosystem?*

---

## 💡 The NexusIQ Solution

**NexusIQ** is a universal, modular AI energy orchestration platform that turns energy telemetry and utility bills into automated, explainable, and cost-saving actions.

### Core Capabilities
1. **Universal 3-Tier Adaptability:**
   - **Level 1 — Basic (Zero New Hardware):** Works strictly from electricity bills or historical CSV meter reads. Provides baseload vampire leakage detection, tariff optimization, and peak-shaving recommendations.
   - **Level 2 — Solar & Smart Meter:** Integrates rooftop solar PV, ambient weather telemetry (irradiance, cloud index, cooling degree hours), and dual-stream neural forecasting.
   - **Level 3 — Intelligent Campus (Microgrid):** Full digital twin across 5 campus buildings, Battery Energy Storage Systems (BESS), automated load scheduling, and sub-meter telemetry.
2. **Dual AI Forecasting Engine:**
   - **Electricity Demand Prediction:** Time-of-day, academic calendar, occupancy schedule, and cooling degree thermal sensitivity (+3.8% demand / °C above 24°C).
   - **Renewable Solar Prediction:** Physical Sandia PV optics, Global Horizontal Irradiance (GHI), cloud attenuation, and temperature derating.
3. **HiGHS Mathematical Optimization Solver (MILP):**
   - Coordinates renewable generation, battery charging/discharging, flexible load shifting, Time-of-Use tariffs, and contracted demand charges.
   - Enforces strict physical energy conservation:
     $$\sum P_{\text{grid}}(t) + P_{\text{solar}}(t) + P_{\text{discharge}}(t) = P_{\text{demand}}(t) + P_{\text{charge}}(t) + P_{\text{shifted}}(t)$$
   - Graceful resource degradation: dynamically solves even when solar = 0, battery = 0, or tariff is flat.
4. **Transparent & Explainable Recommendations:**
   - Every recommendation explains *why* the action is advised, its *exact energy impact (kWh)*, its *financial impact (₹ saved)*, and its *operational constraints* (e.g. water tanks filled before 17:00, HVAC comfort band within ±1.2°C, battery reserve ≥ 20%).
5. **Interactive Campus Digital Twin & What-If Simulator:**
   - Real-time animated power flow diagrams with live conservation validation (0.0 kW delta).
   - What-If sliders for solar expansion, battery sizing, tariff shocks, and monsoon cloud cover.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Ingestion ["1. Universal Ingestion Layer"]
        CSV[Utility Bills & Smart Meter CSVs] --> Normalizer[Data Normalizer & Profiler]
        IoT[BMS & Weather Telemetry] --> Normalizer
    end

    subgraph Core ["2. AI & Optimization Engine (FastAPI)"]
        Normalizer --> Profiler[Campus Energy Profile (L1/L2/L3)]
        Profiler --> Forecast[AI Forecasting & Anomaly Engine<br/>• Demand Prediction<br/>• Solar PV Optics<br/>• Baseload Anomaly Detection]
        Forecast --> Solver[HiGHS Linear Programming Solver<br/>• Battery Dispatch<br/>• Flexible Load Shifter<br/>• ToU Tariff Arbitrage]
    end

    subgraph UI ["3. Interactive Dashboard (React 19 + Tailwind)"]
        Solver --> Dash[Executive KPI Dashboard]
        Solver --> Twin[Campus Digital Twin & Submetering]
        Solver --> Sim[What-If Scenario Simulator]
        Solver --> Reports[ESG & Carbon Offset Audit]
    end
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Node.js**: v18+ (tested on Node v24)
- **Python**: 3.10+ (tested on Python 3.14)

### Running the Application

#### Option A: Quick Runner (PowerShell)
```powershell
.\run_dev.ps1
```

#### Option B: Manual Execution

**1. Start Backend Engine:**
```powershell
python start_backend.py
# Backend runs on http://127.0.0.1:8000
# Interactive OpenAPI Swagger Docs: http://127.0.0.1:8000/docs
```

**2. Start Frontend UI:**
```powershell
cd frontend
npm run dev
# Frontend runs on http://localhost:3000
```

---

## 🧪 Verification & Testing

Run the automated backend test suite:
```powershell
cd backend
python test_backend.py
```

### Verified Test Results (12 / 12 Tests Passed)
- ✅ **Zero Solar & Zero Battery (Level 1)**: Correctly models facility with zero renewable capacity, solving dispatch via flexible loads.
- ✅ **Solar without Battery (Level 2)**: Solves direct solar self-consumption without battery storage.
- ✅ **Battery without Solar**: Solves pure Time-of-Use tariff arbitrage and peak shaving.
- ✅ **Full Solar & Battery (Level 3)**: Solved global optimal 24h dispatch saving **₹10,243/day** and shaving **133 kW** peak grid import.
- ✅ **Battery Reserve & Efficiency**: Respects 25% min and 90% max SoC bounds with roundtrip efficiency.
- ✅ **Mutual Exclusivity**: Binary indicators guarantee zero simultaneous charging and discharging across all intervals.
- ✅ **Flexible Load Deadlines**: Individual operating windows and deadlines enforced with 100% required energy satisfied.
- ✅ **Energy Conservation**: Complete power balance verified for all 24 intervals (max delta < 0.1 kW).
- ✅ **15-Min & Multi-Interval CSV Ingestion**: Chronological sorting, kW/kWh differentiation, and interval duration calculation verified.
- ✅ **Tariff Flexibility**: Validated for both Flat Rate and Time-of-Use tariff regimes.
- ✅ **What-If Integrity**: Verified actual peak grid demand output (kW) and non-zero simulation metrics.
- ✅ **Error & Anomaly Handling**: Gracefully handles corrupt, duplicate, and missing CSV records with quality audit notes.

---

## 📊 Deployment Levels Overview

| Feature | Level 1: Basic | Level 2: Solar | Level 3: Microgrid |
| :--- | :---: | :---: | :---: |
| **Hardware Required** | **None** (Bills / CSV) | Solar PV Inverter | Solar + BESS + BMS |
| **Target User** | Small Colleges / Offices | Rooftop Solar Schools | University Campuses / Hospitals |
| **Forecasting** | Demand + Anomaly | Demand + Solar PV + Weather | Full Microgrid Predictive |
| **Optimization** | Tariff Peak Shifting | Solar Self-Consumption | Full Battery & Load Arbitrage |
| **Digital Twin** | Virtual Profile | Inverter + Grid Telemetry | 5-Building Submeter Twin |

---

## 👥 Team EcoNexus
- **Institution:** New Horizon College of Engineering (NHCE)
- **Competition:** Ideathon 2026 National Level
- **Platform:** NexusIQ — Predict. Optimize. Sustain.

