import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.dataset_manager import dataset_manager

client = TestClient(app)

def test_complete_dynamic_pipeline():
    print("\n=======================================================")
    print("Testing NexusIQ Complete Dynamic Data Integration Pipeline")
    print("=======================================================")

    # ---------------------------------------------------------
    # 1. VERIFY INITIAL DEMO BENCHMARK STATE
    # ---------------------------------------------------------
    status_res = client.get("/api/dataset/status")
    assert status_res.status_code == 200
    status = status_res.json()
    print(f"\n[1] Initial State: {status['source_type']} | {status['filename']}")
    assert status["source_type"] == "demo"
    assert "nhce_smart_meter_sample.csv" in status["filename"]

    dash_initial = client.get("/api/dashboard/live").json()
    demo_consumption = dash_initial["kpis"]["total_consumption_kwh"]
    demo_peak = dash_initial["kpis"]["grid_consumption_kwh"]
    print(f"    Demo Total Consumption: {demo_consumption:,.1f} kWh")

    # ---------------------------------------------------------
    # 2. UPLOAD DATASET A (Tech Park: ~11,159 kWh, Solar PV)
    # ---------------------------------------------------------
    file_a_path = os.path.join(os.path.dirname(__file__), "test_data", "dataset_a_tech_park.csv")
    with open(file_a_path, "rb") as f:
        res_a = client.post("/api/upload-csv", files={"file": ("dataset_a_tech_park.csv", f, "text/csv")})
    assert res_a.status_code == 200
    summary_a = res_a.json()
    print(f"\n[2] Uploaded Dataset A: '{summary_a['filename']}'")
    print(f"    Records: {summary_a['total_records']}, Format: {summary_a['detected_format']}")
    print(f"    Total Consumption: {summary_a['total_consumption_kwh']} kWh, Peak: {summary_a['peak_recorded_demand_kw']} kW")
    assert summary_a["has_solar_in_csv"] is True
    assert summary_a["inferred_level"] == "level_2_solar"

    # Verify Active Dataset Status
    status_a = client.get("/api/dataset/status").json()
    assert status_a["source_type"] == "uploaded"
    assert status_a["filename"] == "dataset_a_tech_park.csv"
    assert status_a["has_solar"] is True

    # Verify Dashboard recalculation for Dataset A
    dash_a = client.get("/api/dashboard/live").json()
    assert dash_a["active_dataset"]["filename"] == "dataset_a_tech_park.csv"
    assert dash_a["kpis"]["total_consumption_kwh"] == summary_a["total_consumption_kwh"]
    assert dash_a["kpis"]["solar_generation_kwh"] > 1000.0
    print(f"    Dashboard Live KPIs for Dataset A verified: {dash_a['kpis']['total_consumption_kwh']} kWh (Solar: {dash_a['kpis']['solar_generation_kwh']} kWh)")

    # Verify Forecast model trained on Dataset A
    fc_a = client.get("/api/forecast/24h?cloud_cover=15").json()
    assert fc_a["actual_demand_kw"][12] == 960.2 # Hour 12 peak from Dataset A
    assert fc_a["actual_demand_kw"][0] == 145.2 # Hour 0 from Dataset A
    assert max(fc_a["solar_forecast_kw"]) > 200.0 # Active solar from Dataset A
    print(f"    Forecast actual series matches Dataset A: Hour 0 = {fc_a['actual_demand_kw'][0]} kW, Hour 12 = {fc_a['actual_demand_kw'][12]} kW")

    # Verify Optimization uses Dataset A
    opt_a = client.post("/api/optimize").json()
    cost_a = opt_a["total_cost_optimized_inr"]
    savings_a = opt_a["cost_savings_inr"]
    print(f"    Optimization for Dataset A: Cost = INR {cost_a:,.2f}, Savings = INR {savings_a:,.2f}")
    assert cost_a > 0

    # ---------------------------------------------------------
    # 3. UPLOAD DATASET B (Heavy Industry: ~108,767 kWh, NO Solar)
    # ---------------------------------------------------------
    file_b_path = os.path.join(os.path.dirname(__file__), "test_data", "dataset_b_heavy_industry.csv")
    with open(file_b_path, "rb") as f:
        res_b = client.post("/api/upload-csv", files={"file": ("dataset_b_heavy_industry.csv", f, "text/csv")})
    assert res_b.status_code == 200
    summary_b = res_b.json()
    print(f"\n[3] Uploaded Dataset B: '{summary_b['filename']}'")
    print(f"    Records: {summary_b['total_records']}, Total: {summary_b['total_consumption_kwh']} kWh, Peak: {summary_b['peak_recorded_demand_kw']} kW")
    assert summary_b["has_solar_in_csv"] is False
    assert summary_b["inferred_level"] == "level_1_basic"

    # Verify Active Dataset Status changed
    status_b = client.get("/api/dataset/status").json()
    assert status_b["source_type"] == "uploaded"
    assert status_b["filename"] == "dataset_b_heavy_industry.csv"
    assert status_b["has_solar"] is False

    # Verify Dashboard completely changed and reflects Dataset B
    dash_b = client.get("/api/dashboard/live").json()
    assert dash_b["active_dataset"]["filename"] == "dataset_b_heavy_industry.csv"
    assert dash_b["kpis"]["total_consumption_kwh"] == summary_b["total_consumption_kwh"]
    assert dash_b["kpis"]["solar_generation_kwh"] == 0.0 # ZERO SOLAR
    assert dash_b["kpis"]["solar_generation_trend"] == "No Solar Installed"
    assert dash_b["kpis"]["battery_status"] == "N/A (No Storage Installed)"
    print(f"    Dashboard Live KPIs for Dataset B verified: {dash_b['kpis']['total_consumption_kwh']} kWh (Zero Solar, No Storage)")

    # Crucial Demonstration: Dataset A vs Dataset B metrics are drastically different!
    assert dash_b["kpis"]["total_consumption_kwh"] > 9 * dash_a["kpis"]["total_consumption_kwh"]
    print(f"    [VERIFIED] Dataset B consumption ({dash_b['kpis']['total_consumption_kwh']}) is ~10x Dataset A ({dash_a['kpis']['total_consumption_kwh']})")

    # Verify Forecast for Dataset B
    fc_b = client.get("/api/forecast/24h?cloud_cover=15").json()
    assert fc_b["actual_demand_kw"][12] == 4850.4 # Hour 12 from Dataset B
    assert fc_b["solar_forecast_kw"] == [0.0] * 24 # ZERO SOLAR INVENTED!
    print(f"    Forecast actual series matches Dataset B: Hour 12 = {fc_b['actual_demand_kw'][12]} kW, Solar = 0.0 kW")

    # Verify Optimization for Dataset B
    opt_b = client.post("/api/optimize").json()
    cost_b = opt_b["total_cost_optimized_inr"]
    print(f"    Optimization for Dataset B: Cost = INR {cost_b:,.2f}")
    assert cost_b > 5 * cost_a

    # ---------------------------------------------------------
    # 4. TEST CSV VALIDATION & REJECTION FOR INVALID COLUMNS
    # ---------------------------------------------------------
    file_c_path = os.path.join(os.path.dirname(__file__), "test_data", "dataset_c_invalid.csv")
    with open(file_c_path, "rb") as f:
        res_c = client.post("/api/upload-csv", files={"file": ("dataset_c_invalid.csv", f, "text/csv")})
    print(f"\n[4] Tested Invalid CSV Upload: Status = {res_c.status_code}")
    assert res_c.status_code == 400
    err_detail = res_c.json()["detail"]
    print(f"    Proper validation error returned: '{err_detail}'")
    assert "validation failed" in err_detail.lower() or "no numeric" in err_detail.lower()

    # Verify active dataset was NOT corrupted by the invalid upload
    status_post_c = client.get("/api/dataset/status").json()
    assert status_post_c["filename"] == "dataset_b_heavy_industry.csv"
    print(f"    Active dataset integrity preserved after failed upload: '{status_post_c['filename']}'")

    # ---------------------------------------------------------
    # 5. TEST SWITCHING BACK TO DEMO MODE
    # ---------------------------------------------------------
    switch_res = client.post("/api/dataset/switch-mode", json={"mode": "demo", "level": "level_3_campus"})
    assert switch_res.status_code == 200
    status_demo = switch_res.json()
    print(f"\n[5] Switched back to Demo Mode: {status_demo['source_type']} | {status_demo['filename']}")
    assert status_demo["source_type"] == "demo"
    assert "nhce_smart_meter_sample.csv" in status_demo["filename"]

    dash_demo = client.get("/api/dashboard/live").json()
    assert dash_demo["active_dataset"]["source_type"] == "demo"
    print(f"    Dashboard successfully restored to Demo Benchmark ({dash_demo['kpis']['total_consumption_kwh']} kWh)")

    print("\n=======================================================")
    print("[SUCCESS] Complete Dynamic Data Pipeline Verified 100%!")
    print("=======================================================")

if __name__ == "__main__":
    test_complete_dynamic_pipeline()
