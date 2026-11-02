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
from .dataset_manager import dataset_manager
from .csv_parser import parse_energy_csv
from .forecasting import run_ai_forecast
from .optimization import run_energy_optimization
from .simulator import get_live_energy_flow_state, simulate_what_if

app = FastAPI(
    title="NexusIQ - AI-Powered Energy Management & Optimization Engine",
    description="Universal energy orchestration for buildings and campuses (Ideathon 2026 - Team EcoNexus)",
    version="1.0.0"
)

ALLOWED_ORIGINS = os.getenv(
    "NEXUSIQ_CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000,http://localhost:8001,http://127.0.0.1:8001"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

REMEDIATED_ANOMALIES: set = set()
BUILDING_OVERRIDES: Dict[str, Dict[str, Any]] = {}

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "platform": "NexusIQ AI-Powered Energy Management Platform",
        "institution": "NHCE - Team EcoNexus",
        "competition": "Ideathon 2026",
        "version": "1.0.0",
        "active_dataset": dataset_manager.active.display_name
    }

# -------------------------------------------------------------
# CENTRALIZED DATASET STATE & SOURCE OF TRUTH
# -------------------------------------------------------------
@app.get("/api/dataset/status")
def get_dataset_status():
    """
    Returns the current active dataset state (single source of truth).
    """
    return dataset_manager.active.to_dict()

@app.post("/api/dataset/switch-mode")
def switch_dataset_mode(payload: Dict[str, Any] = Body(...)):
    """
    Switches between Demo Mode and Uploaded Data Mode.
    """
    mode = payload.get("mode", "demo")
    level = payload.get("level", "level_3_campus")
    if mode == "demo":
        dataset_manager.switch_to_demo(level)
    return dataset_manager.active.to_dict()

@app.get("/api/profile", response_model=FacilityConfig)
def get_facility_profile():
    return dataset_manager.get_facility_config()

@app.post("/api/profile/switch", response_model=FacilityConfig)
def switch_deployment_level(level: DeploymentLevel):
    active = dataset_manager.active
    if active.source_type == "demo":
        dataset_manager.switch_to_demo(level)
    else:
        active.inferred_level = level
        if level == "level_1_basic":
            active.has_solar = False
            active.has_battery = False
        elif level == "level_2_solar":
            active.has_solar = True
            active.has_battery = False
        else:
            active.has_solar = True
            active.has_battery = True
    return dataset_manager.get_facility_config()

@app.post("/api/settings", response_model=FacilityConfig)
def update_settings(config: FacilityConfig):
    active = dataset_manager.active
    active.has_solar = config.has_solar
    active.solar_installed_capacity_kw = config.solar_installed_capacity_kw
    active.has_battery = config.has_battery
    active.battery_capacity_kwh = config.battery_capacity_kwh
    active.battery_max_power_kw = config.battery_max_power_kw
    active.inferred_level = config.level
    return dataset_manager.get_facility_config()

# -------------------------------------------------------------
# DYNAMIC DASHBOARD (Derives metrics strictly from active dataset)
# -------------------------------------------------------------
@app.get("/api/dashboard/live")
def get_live_dashboard():
    active = dataset_manager.active
    facility = dataset_manager.get_facility_config()

    flow = get_live_energy_flow_state(
        facility,
        simulated_hour=13,
        active_demand_24h=active.demand_24h,
        active_solar_24h=active.solar_24h,
        data_source_label=f"{'Uploaded' if active.source_type == 'uploaded' else 'Demo'}: {active.filename}"
    )

    forecast = run_ai_forecast(
        facility,
        custom_demand_24h=active.demand_24h,
        custom_solar_24h=active.solar_24h
    )

    filtered_anomalies = [a for a in forecast.anomalies if a.id not in REMEDIATED_ANOMALIES]
    forecast.anomalies = filtered_anomalies

    opt = run_energy_optimization(
        facility,
        forecast.forecast_demand_kw,
        forecast.solar_forecast_kw
    )

    total_consumption_kwh = active.total_consumption_kwh
    solar_generation_kwh = active.total_solar_kwh if active.has_solar else 0.0
    grid_consumption_kwh = sum(opt.schedule.optimized_grid_kw)
    estimated_cost_inr = opt.total_cost_optimized_inr
    co2_emissions_avoided_tons = opt.co2_avoided_tons

    cost_trend = f"{opt.metrics_summary[0].change_percent:+.1f}% vs baseline"
    grid_trend = f"{opt.metrics_summary[1].change_percent:+.1f}% vs baseline"
    co2_trend = f"{opt.metrics_summary[3].change_percent:+.1f}% vs baseline"

    battery_status = "Standby"
    if facility.has_battery:
        if flow.battery_flow_kw < -1.0:
            battery_status = "Charging (Surplus)"
        elif flow.battery_flow_kw > 1.0:
            battery_status = "Discharging (Peak Shaving)"

    solar_trend = (
        ("Active Ingested PV Telemetry" if active.source_type == "uploaded" else "Sandia PV Physical Output")
        if active.has_solar else "No Solar Installed"
    )

    return {
        "facility_name": facility.name,
        "deployment_level": facility.level,
        "active_dataset": active.to_dict(),
        "kpis": {
            "total_consumption_kwh": round(total_consumption_kwh, 1),
            "total_consumption_trend": f"Dataset Total ({active.total_records} intervals)",
            "solar_generation_kwh": round(solar_generation_kwh, 1),
            "solar_generation_trend": solar_trend,
            "battery_soc_percent": flow.battery_soc_percent if facility.has_battery else 0.0,
            "battery_status": battery_status if facility.has_battery else "N/A (No Storage Installed)",
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
            "historical_data": f"{'Uploaded' if active.source_type == 'uploaded' else 'Demo'}: {active.filename}",
            "ai_models": "Ridge Regression & HiGHS MILP Solver",
            "hardware_automation": "Simulation Mode (API Ready)"
        }
    }

# -------------------------------------------------------------
# DYNAMIC FORECASTING (Trained on Active Dataset)
# -------------------------------------------------------------
@app.get("/api/forecast/24h", response_model=ForecastResponse)
def get_24h_forecast(cloud_cover: float = 15.0):
    if not (0.0 <= cloud_cover <= 100.0):
        raise HTTPException(status_code=400, detail="cloud_cover must be between 0.0 and 100.0")

    active = dataset_manager.active
    facility = dataset_manager.get_facility_config()

    res = run_ai_forecast(
        facility,
        custom_demand_24h=active.demand_24h,
        custom_solar_24h=active.solar_24h,
        cloud_cover_percent=cloud_cover
    )
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

# -------------------------------------------------------------
# DYNAMIC OPTIMIZATION (Uses Active Dataset as Baseline)
# -------------------------------------------------------------
@app.post("/api/optimize", response_model=OptimizationResponse)
def run_optimization(flexible_shift_enabled: bool = True):
    active = dataset_manager.active
    facility = dataset_manager.get_facility_config()

    forecast = run_ai_forecast(
        facility,
        custom_demand_24h=active.demand_24h,
        custom_solar_24h=active.solar_24h
    )

    return run_energy_optimization(
        facility,
        forecast.forecast_demand_kw,
        forecast.solar_forecast_kw,
        flexible_shift_enabled=flexible_shift_enabled
    )

@app.get("/api/optimization/download-schedule-csv")
def download_schedule_csv():
    active = dataset_manager.active
    facility = dataset_manager.get_facility_config()

    forecast = run_ai_forecast(facility, custom_demand_24h=active.demand_24h, custom_solar_24h=active.solar_24h)
    opt = run_energy_optimization(facility, forecast.forecast_demand_kw, forecast.solar_forecast_kw)
    sch = opt.schedule
    lines = ["hour,time,baseline_grid_kw,optimized_grid_kw,solar_utilized_kw,battery_charge_kw,battery_discharge_kw,battery_soc_percent,shifted_load_kw"]
    for i, t in enumerate(sch.hours):
        lines.append(f"{t},{sch.time_labels[i]},{sch.baseline_grid_kw[i]},{sch.optimized_grid_kw[i]},{sch.solar_utilized_kw[i]},{sch.battery_charge_kw[i]},{sch.battery_discharge_kw[i]},{sch.battery_soc_percent[i]},{sch.shifted_load_kw[i]}")
    return PlainTextResponse(
        content="\n".join(lines),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=nexusiq_optimized_dispatch_schedule.csv"}
    )

# -------------------------------------------------------------
# WHAT-IF SIMULATOR (Derived from Active Dataset)
# -------------------------------------------------------------
@app.post("/api/what-if", response_model=WhatIfResponse)
def run_what_if_analysis(req: WhatIfRequest):
    active = dataset_manager.active
    facility = dataset_manager.get_facility_config()
    return simulate_what_if(
        req,
        facility,
        active_demand_24h=active.demand_24h,
        active_solar_24h=active.solar_24h
    )

# -------------------------------------------------------------
# CSV INGESTION & DATASET SWITCHING
# -------------------------------------------------------------
@app.post("/api/upload-csv", response_model=CSVUploadSummary)
async def upload_energy_csv(file: UploadFile = File(...)):
    try:
        content = await file.read()
        summary, norm_data = parse_energy_csv(content, file.filename or "uploaded.csv")
        dataset_manager.set_uploaded_dataset(summary, norm_data)
        REMEDIATED_ANOMALIES.clear()
        BUILDING_OVERRIDES.clear()
        return summary
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV file: {str(e)}")

@app.post("/api/load-sample", response_model=CSVUploadSummary)
def load_sample_dataset():
    sample_text = generate_sample_csv_content().encode('utf-8')
    summary, norm_data = parse_energy_csv(sample_text, "nhce_smart_meter_sample.csv")
    dataset_manager.set_uploaded_dataset(summary, norm_data)
    REMEDIATED_ANOMALIES.clear()
    BUILDING_OVERRIDES.clear()
    return summary

@app.get("/api/download-sample-csv")
def download_sample_csv():
    csv_text = generate_sample_csv_content()
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=nexusiq_sample_energy_data.csv"}
    )

# -------------------------------------------------------------
# DIGITAL TWIN SUBMETERS
# -------------------------------------------------------------
@app.get("/api/campus/buildings", response_model=List[BuildingLoad])
def get_campus_building_loads():
    active = dataset_manager.active
    facility = dataset_manager.get_facility_config()

    if active.has_submeters and active.buildings:
        blds = [b.model_copy() for b in active.buildings]
    elif active.source_type == "uploaded" and active.buildings:
        blds = [b.model_copy() for b in active.buildings]
    else:
        blds = get_campus_buildings(facility.level)

    for b in blds:
        if b.id in BUILDING_OVERRIDES:
            over = BUILDING_OVERRIDES[b.id]
            b.current_load_kw = over.get("current_load_kw", b.current_load_kw)
            b.operational_status = over.get("operational_status", b.operational_status)

    return blds

@app.post("/api/buildings/{bld_id}/toggle-shift")
def toggle_building_load_shift(bld_id: str):
    active = dataset_manager.active
    facility = dataset_manager.get_facility_config()
    buildings = get_campus_building_loads()
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
