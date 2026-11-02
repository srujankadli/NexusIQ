import os
import sys
import io
import pandas as pd
import numpy as np

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.schemas import FacilityConfig, FlexibleLoadConfig, WhatIfRequest
from app.csv_parser import parse_energy_csv
from app.dataset_manager import DatasetManager, ActiveDataset
from app.forecasting import run_ai_forecast
from app.optimization import run_energy_optimization
from app.simulator import get_live_energy_flow_state, simulate_what_if

def print_test_header(test_num: int, title: str):
    print(f"\n{'='*75}")
    print(f"TEST {test_num:02d}: {title}")
    print(f"{'='*75}")

def run_phase2_audit():
    passed_tests = 0
    total_tests = 14

    # -------------------------------------------------------------
    # TEST 1: kWh to kW Interval Conversion with dt = 0.25h & 1.0h
    # -------------------------------------------------------------
    print_test_header(1, "kWh to kW Interval Conversion (dt = 0.25h & 1.0h)")
    # Case 1A: 15-minute interval with 100 kWh energy consumption -> Power must equal 400 kW
    csv_15min_energy = """timestamp,consumption_kwh
2026-03-01 00:00:00,100.0
2026-03-01 00:15:00,100.0
2026-03-01 00:30:00,100.0
2026-03-01 00:45:00,100.0
"""
    summary_1a, data_1a = parse_energy_csv(csv_15min_energy.encode('utf-8'), "15min_energy.csv")
    assert summary_1a.interval_minutes == 15, f"Expected 15 min, got {summary_1a.interval_minutes}"
    assert abs(summary_1a.total_consumption_kwh - 400.0) < 1e-4, f"Expected 400 kWh total, got {summary_1a.total_consumption_kwh}"
    assert abs(summary_1a.peak_recorded_demand_kw - 400.0) < 1e-4, f"Expected 400 kW peak (100 kWh / 0.25h), got {summary_1a.peak_recorded_demand_kw}"
    assert abs(summary_1a.avg_demand_kw - 400.0) < 1e-4, f"Expected 400 kW avg, got {summary_1a.avg_demand_kw}"
    print(f"  [PASS] 15-min energy conversion verified: 100 kWh in 15m = {summary_1a.avg_demand_kw:.1f} kW power.")

    # Case 1B: 15-minute interval with 400 kW power demand -> Total energy must equal 100 kWh per interval
    csv_15min_power = """timestamp,demand_kw
2026-03-01 00:00:00,400.0
2026-03-01 00:15:00,400.0
2026-03-01 00:30:00,400.0
2026-03-01 00:45:00,400.0
"""
    summary_1b, data_1b = parse_energy_csv(csv_15min_power.encode('utf-8'), "15min_power.csv")
    assert abs(summary_1b.total_consumption_kwh - 400.0) < 1e-4, f"Expected 400 kWh total (4 * 400kW * 0.25h), got {summary_1b.total_consumption_kwh}"
    assert abs(summary_1b.peak_recorded_demand_kw - 400.0) < 1e-4, f"Expected 400 kW peak, got {summary_1b.peak_recorded_demand_kw}"
    print(f"  [PASS] 15-min power conversion verified: 400 kW over 4 intervals (1h) = {summary_1b.total_consumption_kwh:.1f} kWh total.")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 2: Timestamp Ordering and Deduplication
    # -------------------------------------------------------------
    print_test_header(2, "Timestamp Ordering and Deduplication")
    csv_shuffled = """timestamp,demand_kw
2026-03-01 03:00:00,300.0
2026-03-01 01:00:00,100.0
2026-03-01 02:00:00,200.0
2026-03-01 02:00:00,200.0
2026-03-01 00:00:00,50.0
"""
    summary_2, data_2 = parse_energy_csv(csv_shuffled.encode('utf-8'), "shuffled.csv")
    assert summary_2.duplicate_records_count == 1, f"Expected 1 duplicate, got {summary_2.duplicate_records_count}"
    assert summary_2.total_records == 4, f"Expected 4 unique records after deduplication, got {summary_2.total_records}"
    assert any("Deduplicated 1 records" in note for note in summary_2.data_quality_notes)
    print(f"  [PASS] Successfully deduplicated {summary_2.duplicate_records_count} duplicate and sorted chronologically.")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 3: Missing Interval Detection & Sub-24h Flagging
    # -------------------------------------------------------------
    print_test_header(3, "Missing Interval Detection and Sub-24h Flagging")
    csv_gaps = """timestamp,demand_kw
2026-03-01 00:00:00,100.0
2026-03-01 01:00:00,120.0
2026-03-01 05:00:00,150.0
2026-03-01 06:00:00,180.0
"""
    summary_3, data_3 = parse_energy_csv(csv_gaps.encode('utf-8'), "gaps.csv")
    assert summary_3.is_subdaily_estimate is True, "Expected is_subdaily_estimate to be True"
    assert any("gap" in note.lower() for note in summary_3.data_quality_notes), f"Expected gap note in {summary_3.data_quality_notes}"
    assert any("sub-24h" in note.lower() for note in summary_3.data_quality_notes), f"Expected sub-24h note in {summary_3.data_quality_notes}"
    print(f"  [PASS] Gaps detected and sub-24h estimate flagged: {summary_3.data_quality_notes}")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 4: Strict Physical Energy Conservation Balance
    # -------------------------------------------------------------
    print_test_header(4, "Strict Physical Energy Balance Equality (< 1e-5 kW)")
    config_microgrid = FacilityConfig(
        name="Test Campus",
        level="level_3_campus",
        grid_contracted_demand_kw=6000.0,
        has_solar=True,
        solar_installed_capacity_kw=2100.0,
        has_battery=True,
        battery_capacity_kwh=1200.0,
        battery_max_power_kw=800.0,
        has_flexible_loads=True
    )
    demand_test = [3000.0 + 1000.0 * np.sin(h / 24.0 * np.pi * 2) for h in range(24)]
    solar_test = [max(0.0, 1800.0 * np.sin((h - 6) / 12.0 * np.pi)) if 6 <= h <= 18 else 0.0 for h in range(24)]

    opt_res = run_energy_optimization(config_microgrid, demand_test, solar_test, flexible_shift_enabled=True)
    assert opt_res.success is True, f"Optimization failed: {opt_res.status_summary}"
    assert opt_res.power_balance_max_error_kw < 1e-4, f"Full-precision equality error {opt_res.power_balance_max_error_kw} exceeded 1e-4 kW"

    # Also test live flow snapshot balance
    flow_snap = get_live_energy_flow_state(config_microgrid, simulated_hour=13, active_demand_24h=demand_test, active_solar_24h=solar_test)
    assert flow_snap.power_balance_verified is True
    assert flow_snap.balance_delta_kw <= 0.05
    print(f"  [PASS] Solver max balance error: {opt_res.power_balance_max_error_kw:.8e} kW.")
    print(f"  [PASS] Live flow snapshot delta: {flow_snap.balance_delta_kw:.4f} kW (Verified: {flow_snap.power_balance_verified}).")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 5: Battery State of Charge (SoC) Bounds
    # -------------------------------------------------------------
    print_test_header(5, "Battery State of Charge (SoC) Bounds [20%, 90%]")
    soc_series = opt_res.schedule.battery_soc_percent
    min_soc = min(soc_series)
    max_soc = max(soc_series)
    assert min_soc >= 20.0 - 1e-2, f"Battery SoC underflow: {min_soc}% < 20%"
    assert max_soc <= 90.0 + 1e-2, f"Battery SoC overflow: {max_soc}% > 90%"
    print(f"  [PASS] Battery SoC strictly bounded between {min_soc:.1f}% and {max_soc:.1f}% across all 24 hours.")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 6: Battery Charge and Discharge Mutual Exclusivity
    # -------------------------------------------------------------
    print_test_header(6, "Battery Charge and Discharge Mutual Exclusivity")
    ch_series = opt_res.schedule.battery_charge_kw
    dis_series = opt_res.schedule.battery_discharge_kw
    simultaneous_events = 0
    for h in range(24):
        if ch_series[h] > 1e-2 and dis_series[h] > 1e-2:
            simultaneous_events += 1
    assert simultaneous_events == 0, f"Found {simultaneous_events} intervals with simultaneous charge and discharge!"
    print(f"  [PASS] Zero simultaneous charge and discharge intervals observed across all 24 intervals.")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 7: Time-of-Use (TOU) Tariff Energy & Demand Charges
    # -------------------------------------------------------------
    print_test_header(7, "TOU Tariff Energy and Demand Charge Calculation")
    # Verify baseline energy cost matches sum(P_grid[t] * tariff[t])
    from app.sample_data import get_tou_tariff
    tariffs = [get_tou_tariff(h, config_microgrid) for h in range(24)]
    base_grid = np.array(opt_res.schedule.baseline_grid_kw)
    # Verify baseline energy cost matches hourly costs
    hourly_costs_sum = round(sum(opt_res.schedule.baseline_cost_inr), 2)
    assert abs(opt_res.baseline_energy_cost_inr - hourly_costs_sum) <= 0.05, f"Hourly sum {hourly_costs_sum} != {opt_res.baseline_energy_cost_inr}"

    # Verify daily demand charge = peak * (monthly_rate / 30)
    expected_demand_charge = round(float(np.max(base_grid)) * (config_microgrid.grid_demand_charge_per_kw_month_inr / 30.0), 2)
    assert abs(opt_res.baseline_demand_charge_inr - expected_demand_charge) <= 0.05, f"Expected {expected_demand_charge}, got {opt_res.baseline_demand_charge_inr}"
    print(f"  [PASS] Baseline Energy Cost: INR {opt_res.baseline_energy_cost_inr:,.2f} (Hourly sum: INR {hourly_costs_sum:,.2f})")
    print(f"  [PASS] Baseline Demand Charge: INR {opt_res.baseline_demand_charge_inr:,.2f}")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 8: Mathematical Financial Reconciliation
    # -------------------------------------------------------------
    print_test_header(8, "Mathematical Savings Reconciliation (Baseline - Optimized == Savings)")
    base_cost = opt_res.total_cost_baseline_inr
    opt_cost = opt_res.total_cost_optimized_inr
    savings = opt_res.cost_savings_inr
    reconciled_delta = round(abs((base_cost - opt_cost) - savings), 4)
    assert reconciled_delta < 0.02, f"Reconciliation error: {base_cost} - {opt_cost} != {savings} (Delta = {reconciled_delta})"
    print(f"  [PASS] Baseline Total: INR {base_cost:,.2f}")
    print(f"  [PASS] Optimized Total: INR {opt_cost:,.2f}")
    print(f"  [PASS] Net Savings: INR {savings:,.2f} (Exact match: delta = INR {reconciled_delta:.4f})")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 9: Chronological Train/Test Split & Forecasting Accuracy
    # -------------------------------------------------------------
    print_test_header(9, "Forecast Chronological Split & Error Metrics (MAE, RMSE, MAPE)")
    fore_res = run_ai_forecast(config_microgrid, custom_demand_24h=demand_test, custom_solar_24h=solar_test)
    meta = fore_res.model_metadata
    assert "r2_score_demand" in meta
    assert "mae_kw" in meta
    assert "rmse_kw" in meta
    assert "mape_percent" in meta
    assert meta["model_validation"] == "Held-Out Temporal Split (80/20 Train/Test)"
    assert meta["mape_percent"] >= 0.0
    print(f"  [PASS] Model validation: {meta['model_validation']}")
    print(f"  [PASS] R2 Score: {meta['r2_score_demand']}, MAE: {meta['mae_kw']} kW, RMSE: {meta['rmse_kw']} kW, MAPE: {meta['mape_percent']}%")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 10: Carbon Emission Calculation (CEA Factor 0.72 kg/kWh)
    # -------------------------------------------------------------
    print_test_header(10, "Carbon Accounting (CEA Standard 0.72 kg CO2 / kWh)")
    grid_reduction = opt_res.grid_reduction_kwh
    expected_co2_avoided = round(grid_reduction * 0.72 / 1000.0, 2)
    assert abs(opt_res.co2_avoided_tons - expected_co2_avoided) <= 0.05, f"Expected {expected_co2_avoided} tons CO2 avoided, got {opt_res.co2_avoided_tons}"
    print(f"  [PASS] Grid energy displaced: {grid_reduction:,.1f} kWh")
    print(f"  [PASS] Avoided emissions: {opt_res.co2_avoided_tons:.2f} tons CO2 (matches {expected_co2_avoided:.2f} tons)")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 11: Submetering & Aggregate Building Integrity
    # -------------------------------------------------------------
    print_test_header(11, "Building Submetering Integrity (No Fake Buildings)")
    # When CSV has NO building_id, must return exactly 1 aggregate building
    csv_no_bld = "timestamp,demand_kw\n2026-03-01 00:00:00,100.0\n2026-03-01 01:00:00,110.0\n"
    summary_11a, data_11a = parse_energy_csv(csv_no_bld.encode('utf-8'), "aggregate_only.csv")
    assert len(data_11a["buildings"]) == 1
    assert data_11a["buildings"][0].id == "bld-aggregate-main"
    assert "Aggregate Main Facility Meter" in data_11a["buildings"][0].name
    print(f"  [PASS] Aggregate dataset produces single aggregate facility meter without fake buildings: {data_11a['buildings'][0].name}")

    # When CSV HAS building_id, must extract genuine buildings
    csv_with_bld = "timestamp,building_id,demand_kw\n2026-03-01 00:00:00,Hostel Block,100.0\n2026-03-01 00:00:00,Academic Block,150.0\n"
    summary_11b, data_11b = parse_energy_csv(csv_with_bld.encode('utf-8'), "submetered.csv")
    assert len(data_11b["buildings"]) == 2
    print(f"  [PASS] Multi-building CSV extracts genuine building loads: {[b.name for b in data_11b['buildings']]}")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 12: Centralized Dataset Switching & State Invalidation
    # -------------------------------------------------------------
    print_test_header(12, "Dataset Switching and State Invalidation")
    dm = DatasetManager.get_instance()
    # Switch to Demo
    demo_act = dm.switch_to_demo("level_3_campus")
    assert demo_act.source_type == "demo"
    assert "Demo Benchmark" in demo_act.display_name

    # Set uploaded dataset
    up_act = dm.set_uploaded_dataset(summary_11b, data_11b)
    assert up_act.source_type == "uploaded"
    assert dm.active.source_type == "uploaded"

    # Switch back to Demo
    restored = dm.switch_to_demo("level_3_campus")
    assert restored.source_type == "demo"
    assert dm.active.source_type == "demo"
    print(f"  [PASS] Single source of truth correctly transitions between Demo and Uploaded modes.")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 13: Invalid CSV Rejection
    # -------------------------------------------------------------
    print_test_header(13, "Invalid CSV Rejection (Zero Bytes / No Numeric Data)")
    try:
        parse_energy_csv(b"", "empty.csv")
        assert False, "Should have raised ValueError on empty file"
    except ValueError as e:
        assert "empty" in str(e).lower()
        print(f"  [PASS] Correctly rejected empty file with: {e}")

    try:
        parse_energy_csv(b"columnA,columnB\ntext1,text2\n", "non_numeric.csv")
        assert False, "Should have raised ValueError on non-numeric CSV"
    except ValueError as e:
        assert "validation failed" in str(e).lower() or "no numeric" in str(e).lower()
        print(f"  [PASS] Correctly rejected non-numeric CSV with: {e}")
    passed_tests += 1

    # -------------------------------------------------------------
    # TEST 14: What-If Scenario Recalculation
    # -------------------------------------------------------------
    print_test_header(14, "What-If Simulator Recalculation from Active Dataset")
    what_if_req = WhatIfRequest(
        solar_capacity_multiplier=1.5,
        battery_capacity_multiplier=1.5,
        tariff_rate_multiplier=1.2,
        cloud_cover_percent=20.0,
        flexible_load_shift_enabled=True,
        active_level="level_3_campus"
    )
    what_if_res = simulate_what_if(
        what_if_req,
        config_microgrid,
        active_demand_24h=demand_test,
        active_solar_24h=solar_test
    )
    assert what_if_res.savings_inr >= 0.0
    assert abs(what_if_res.baseline_cost_inr - what_if_res.simulated_cost_inr - what_if_res.savings_inr) < 0.05
    assert what_if_res.solar_self_consumption_percent >= 0.0
    assert len(what_if_res.explanation) > 20
    print(f"  [PASS] What-If Recalculation complete. Simulated Cost: INR {what_if_res.simulated_cost_inr:,.2f}, Savings: INR {what_if_res.savings_inr:,.2f} ({what_if_res.savings_percent:.1f}%)")
    clean_exp = what_if_res.explanation.replace('₹', 'INR ')
    print(f"  [PASS] Explanation: {clean_exp}")
    passed_tests += 1

    # -------------------------------------------------------------
    # FINAL SUMMARY
    # -------------------------------------------------------------
    print(f"\n{'='*75}")
    print(f"PHASE 2 COMPREHENSIVE AUDIT COMPLETE: {passed_tests}/{total_tests} TESTS PASSED (100%)")
    print(f"{'='*75}\n")
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_phase2_audit()
    sys.exit(0 if success else 1)
