import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from typing import Optional, Dict, Any, List

from .schemas import (
    FacilityConfig,
    DeploymentLevel,
    ForecastResponse,
    OptimizationResponse,
    WhatIfRequest,
    WhatIfResponse,
    CSVUploadSummary,
    EnergyFlowState,
    BuildingLoad
)
from .sample_data import (
    get_campus_buildings,
    generate_sample_csv_content,
    get_tou_tariff
)
from .csv_parser import parse_energy_csv
from .forecasting import run_ai_forecast
from .optimization import run_energy_optimization
from .simulator import get_live_energy_flow_state, simulate_what_if

app = FastAPI(
    title="NexusIQ - AI-Powered Energy Management & Optimization Engine",
    description="Universal energy orchestration for buildings and campuses (Ideathon 2026 - Team EcoNexus)",
    version="1.0.0"
)

# Restrictive & Configurable CORS for Deployment Safety
ALLOWED_ORIGINS = os.getenv(
    "NEXUSIQ_CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Configurable Facility State in memory
CURRENT_FACILITY = FacilityConfig(
    name="NHCE Green Campus",
    level="level_3_campus",
    grid_contracted_demand_kw=6000.0,
    has_solar=True,
    solar_installed_capacity_kw=2100.0,
    has_battery=True,
    battery_capacity_kwh=1200.0,
    battery_max_power_kw=800.0,
    has_flexible_loads=True
)

CUSTOM_DEMAND_DATA: Optional[List[float]] = None
REMEDIATED_ANOMALIES: set = set()
BUILDING_OVERRIDES: Dict[str, Dict[str, Any]] = {}

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "platform": "NexusIQ AI-Powered Energy Management Platform",
        "institution": "NHCE - Team EcoNexus",
        "competition": "Ideathon 2026",
        "version": "1.0.0"
    }

@app.get("/api/profile", response_model=FacilityConfig)
def get_facility_profile():
    return CURRENT_FACILITY

@app.post("/api/profile/switch", response_model=FacilityConfig)
def switch_deployment_level(level: DeploymentLevel):
    global CURRENT_FACILITY
    if level == "level_1_basic":
        CURRENT_FACILITY = FacilityConfig(
            name="NHCE Administrative & Academic Block",
            level="level_1_basic",
            grid_contracted_demand_kw=2500.0,
            has_solar=False,
            solar_installed_capacity_kw=0.0,
            has_battery=False,
            battery_capacity_kwh=0.0,
            battery_max_power_kw=0.0,
            has_flexible_loads=True
        )
    elif level == "level_2_solar":
        CURRENT_FACILITY = FacilityConfig(
            name="NHCE Solar-Equipped Campus Block",
            level="level_2_solar",
            grid_contracted_demand_kw=4000.0,
            has_solar=True,
            solar_installed_capacity_kw=1200.0,
            has_battery=False,
            battery_capacity_kwh=0.0,
            battery_max_power_kw=0.0,
            has_flexible_loads=True
        )
    else:
        CURRENT_FACILITY = FacilityConfig(
            name="NHCE Intelligent Campus",
            level="level_3_campus",
            grid_contracted_demand_kw=6000.0,
            has_solar=True,
            solar_installed_capacity_kw=2100.0,
            has_battery=True,
            battery_capacity_kwh=1200.0,
            battery_max_power_kw=800.0,
            has_flexible_loads=True
        )
    return CURRENT_FACILITY

@app.post("/api/settings", response_model=FacilityConfig)
def update_settings(config: FacilityConfig):
    global CURRENT_FACILITY
    CURRENT_FACILITY = config
    return CURRENT_FACILITY

@app.get("/api/dashboard/live")
def get_live_dashboard():
    flow = get_live_energy_flow_state(CURRENT_FACILITY, simulated_hour=13)
    forecast = run_ai_forecast(CURRENT_FACILITY, custom_demand_24h=CUSTOM_DEMAND_DATA)
    # Filter out remediated anomalies
    filtered_anomalies = [a for a in forecast.anomalies if a.id not in REMEDIATED_ANOMALIES]
    forecast.anomalies = filtered_anomalies

    opt = run_energy_optimization(
        CURRENT_FACILITY,
        forecast.forecast_demand_kw,
        forecast.solar_forecast_kw
    )

    total_consumption_kwh = sum(forecast.actual_demand_kw)
    solar_generation_kwh = sum(forecast.solar_forecast_kw)
    grid_consumption_kwh = sum(opt.schedule.optimized_grid_kw)
    estimated_cost_inr = opt.total_cost_optimized_inr
    co2_emissions_avoided_tons = opt.co2_avoided_tons

    # Derive genuine, non-fabricated trends from backend calculations
    cost_trend = f"{opt.metrics_summary[0].change_percent:+.1f}% vs baseline"
    grid_trend = f"{opt.metrics_summary[1].change_percent:+.1f}% vs baseline"
    co2_trend = f"{opt.metrics_summary[3].change_percent:+.1f}% vs baseline"

    battery_status = "Standby"
    if CURRENT_FACILITY.has_battery:
        if flow.battery_flow_kw < -1.0:
            battery_status = "Charging (Surplus)"
        elif flow.battery_flow_kw > 1.0:
            battery_status = "Discharging (Peak Shaving)"

    return {
        "facility_name": CURRENT_FACILITY.name,
        "deployment_level": CURRENT_FACILITY.level,
        "kpis": {
            "total_consumption_kwh": round(total_consumption_kwh, 1),
            "total_consumption_trend": "Measured Daily Demand",
            "solar_generation_kwh": round(solar_generation_kwh, 1),
            "solar_generation_trend": "Sandia PV Physical Output" if CURRENT_FACILITY.has_solar else "N/A (No Solar Installed)",
            "battery_soc_percent": flow.battery_soc_percent if CURRENT_FACILITY.has_battery else 0.0,
            "battery_status": battery_status if CURRENT_FACILITY.has_battery else "N/A (No Storage Installed)",
            "grid_consumption_kwh": round(grid_consumption_kwh, 1),
            "grid_consumption_trend": grid_trend,
            "estimated_cost_today_inr": round(estimated_cost_inr, 2),
            "estimated_cost_trend": cost_trend,
            "co2_emissions_avoided_tons": round(co2_emissions_avoided_tons, 2),
            "co2_trend": co2_trend
        },
        "energy_flow": flow,
        "active_recommendation": opt.recommendations[0] if opt.recommendations else None,
        "total_anomalies_detected": len(filtered_anomalies),
        "data_fidelity_badges": {
            "historical_data": "Verified Telemetry" if CUSTOM_DEMAND_DATA else "Baseline Operational Profile",
            "ai_models": "Ridge Regression & HiGHS MILP Solver",
            "hardware_automation": "Simulation Mode (API Ready)"
        }
    }

@app.get("/api/forecast/24h", response_model=ForecastResponse)
def get_24h_forecast(cloud_cover: float = 15.0):
    if not (0.0 <= cloud_cover <= 100.0):
        raise HTTPException(status_code=400, detail="cloud_cover must be between 0.0 and 100.0")
    res = run_ai_forecast(CURRENT_FACILITY, custom_demand_24h=CUSTOM_DEMAND_DATA, cloud_cover_percent=cloud_cover)
    res.anomalies = [a for a in res.anomalies if a.id not in REMEDIATED_ANOMALIES]
    return res

@app.post("/api/anomaly/remediate")
def remediate_anomaly(anomaly_id: str = Body(..., embed=True)):
    REMEDIATED_ANOMALIES.add(anomaly_id)
    return {
        "success": True,
        "remediated_id": anomaly_id,
        "execution_mode": "Simulation",
        "message": "Simulation: Virtual BMS interlock script triggered to resolve anomaly."
    }

@app.post("/api/optimize", response_model=OptimizationResponse)
def run_optimization(flexible_shift_enabled: bool = True):
    forecast = run_ai_forecast(CURRENT_FACILITY, custom_demand_24h=CUSTOM_DEMAND_DATA)
    return run_energy_optimization(
        CURRENT_FACILITY,
        forecast.forecast_demand_kw,
        forecast.solar_forecast_kw,
        flexible_shift_enabled=flexible_shift_enabled
    )

@app.get("/api/optimization/download-schedule-csv")
def download_schedule_csv():
    forecast = run_ai_forecast(CURRENT_FACILITY, custom_demand_24h=CUSTOM_DEMAND_DATA)
    opt = run_energy_optimization(CURRENT_FACILITY, forecast.forecast_demand_kw, forecast.solar_forecast_kw)
    sch = opt.schedule
    lines = ["hour,time,baseline_grid_kw,optimized_grid_kw,solar_utilized_kw,battery_charge_kw,battery_discharge_kw,battery_soc_percent,shifted_load_kw"]
    for i, t in enumerate(sch.hours):
        lines.append(f"{t},{sch.time_labels[i]},{sch.baseline_grid_kw[i]},{sch.optimized_grid_kw[i]},{sch.solar_utilized_kw[i]},{sch.battery_charge_kw[i]},{sch.battery_discharge_kw[i]},{sch.battery_soc_percent[i]},{sch.shifted_load_kw[i]}")
    return PlainTextResponse(
        content="\n".join(lines),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=nexusiq_optimized_dispatch_schedule.csv"}
    )

@app.post("/api/what-if", response_model=WhatIfResponse)
def run_what_if_analysis(req: WhatIfRequest):
    return simulate_what_if(req, CURRENT_FACILITY)

@app.post("/api/upload-csv", response_model=CSVUploadSummary)
async def upload_energy_csv(file: UploadFile = File(...)):
    global CUSTOM_DEMAND_DATA
    try:
        content = await file.read()
        summary, norm_data = parse_energy_csv(content, file.filename or "uploaded.csv")
        CUSTOM_DEMAND_DATA = norm_data["demand_24h"]
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV file: {str(e)}")

@app.post("/api/load-sample", response_model=CSVUploadSummary)
def load_sample_dataset():
    global CUSTOM_DEMAND_DATA
    sample_text = generate_sample_csv_content().encode('utf-8')
    summary, norm_data = parse_energy_csv(sample_text, "nhce_smart_meter_sample.csv")
    CUSTOM_DEMAND_DATA = norm_data["demand_24h"]
    return summary

@app.get("/api/download-sample-csv")
def download_sample_csv():
    csv_text = generate_sample_csv_content()
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=nexusiq_sample_energy_data.csv"}
    )

@app.get("/api/campus/buildings", response_model=List[BuildingLoad])
def get_campus_building_loads():
    buildings = get_campus_buildings(CURRENT_FACILITY.level)
    for b in buildings:
        if b.id in BUILDING_OVERRIDES:
            over = BUILDING_OVERRIDES[b.id]
            b.current_load_kw = over.get("current_load_kw", b.current_load_kw)
            b.operational_status = over.get("operational_status", b.operational_status)
    return buildings

@app.post("/api/buildings/{bld_id}/toggle-shift")
def toggle_building_load_shift(bld_id: str):
    buildings = get_campus_buildings(CURRENT_FACILITY.level)
    target = next((b for b in buildings if b.id == bld_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Building not found")
    
    current_status = BUILDING_OVERRIDES.get(bld_id, {}).get("operational_status", target.operational_status)
    if current_status == "Optimized":
        BUILDING_OVERRIDES[bld_id] = {
            "operational_status": "High Demand",
            "current_load_kw": target.current_load_kw + target.flexible_capacity_kw
        }
    else:
        BUILDING_OVERRIDES[bld_id] = {
            "operational_status": "Optimized",
            "current_load_kw": max(target.base_load_kw, target.current_load_kw - target.flexible_capacity_kw)
        }
    return {
        "success": True,
        "bld_id": bld_id,
        "execution_mode": "Simulation",
        "updated": BUILDING_OVERRIDES[bld_id]
    }
