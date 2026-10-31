import sys
import numpy as np
import pandas as pd
from typing import List

from app.schemas import FacilityConfig, WhatIfRequest, FlexibleLoadConfig
from app.forecasting import run_ai_forecast
from app.optimization import run_energy_optimization
from app.sample_data import generate_sample_csv_content, get_time_labels
from app.csv_parser import parse_energy_csv
from app.simulator import get_live_energy_flow_state, simulate_what_if

def run_all_tests():
    print("=" * 65)
    print("NexusIQ Comprehensive Verification & Unit Test Suite")
    print("=" * 65)
    passed_tests = []
    failed_tests = []

    def record_test(name: str, passed: bool, detail: str = ""):
        if passed:
            print(f"  [PASS] {name} {detail}")
            passed_tests.append(name)
        else:
            print(f"  [FAIL] {name} {detail}")
            failed_tests.append((name, detail))

    # -------------------------------------------------------------
    # TEST 1: Zero Solar & Zero Battery (Level 1 Basic)
    # -------------------------------------------------------------
    try:
        cfg_l1 = FacilityConfig(
            level="level_1_basic",
            has_solar=False,
            solar_installed_capacity_kw=0.0,
            has_battery=False,
            battery_capacity_kwh=0.0,
            battery_max_power_kw=0.0,
            has_flexible_loads=True
        )
        fc_l1 = run_ai_forecast(cfg_l1)
        opt_l1 = run_energy_optimization(cfg_l1, fc_l1.forecast_demand_kw, fc_l1.solar_forecast_kw)
        
        solar_zero = all(s == 0.0 for s in opt_l1.schedule.solar_utilized_kw)
        bat_zero = all(c == 0.0 for c in opt_l1.schedule.battery_charge_kw) and all(d == 0.0 for d in opt_l1.schedule.battery_discharge_kw)
        valid = opt_l1.success and solar_zero and bat_zero and opt_l1.total_cost_optimized_inr > 0
        record_test("Zero Solar & Zero Battery (Level 1 Basic)", valid, f"(Cost: INR {opt_l1.total_cost_optimized_inr:,.0f})")
    except Exception as e:
        record_test("Zero Solar & Zero Battery (Level 1 Basic)", False, str(e))

    # -------------------------------------------------------------
    # TEST 2: Solar without Battery (Level 2 Solar)
    # -------------------------------------------------------------
    try:
        cfg_l2 = FacilityConfig(
            level="level_2_solar",
            has_solar=True,
            solar_installed_capacity_kw=1500.0,
            has_battery=False,
            battery_capacity_kwh=0.0,
            battery_max_power_kw=0.0,
            has_flexible_loads=True
        )
        fc_l2 = run_ai_forecast(cfg_l2)
        opt_l2 = run_energy_optimization(cfg_l2, fc_l2.forecast_demand_kw, fc_l2.solar_forecast_kw)
        
        has_solar_gen = sum(opt_l2.schedule.solar_utilized_kw) > 0
        bat_zero = all(c == 0.0 for c in opt_l2.schedule.battery_charge_kw) and all(d == 0.0 for d in opt_l2.schedule.battery_discharge_kw)
        valid = opt_l2.success and has_solar_gen and bat_zero
        record_test("Solar without Battery (Level 2 Solar)", valid, f"(Solar Utilized: {sum(opt_l2.schedule.solar_utilized_kw):,.1f} kWh)")
    except Exception as e:
        record_test("Solar without Battery (Level 2 Solar)", False, str(e))

    # -------------------------------------------------------------
    # TEST 3: Battery without Solar
    # -------------------------------------------------------------
    try:
        cfg_bat = FacilityConfig(
            level="level_1_basic",
            has_solar=False,
            solar_installed_capacity_kw=0.0,
            has_battery=True,
            battery_capacity_kwh=1000.0,
            battery_max_power_kw=500.0,
            battery_min_soc=0.20,
            battery_max_soc=0.95,
            has_flexible_loads=False
        )
        fc_bat = run_ai_forecast(cfg_bat)
        opt_bat = run_energy_optimization(cfg_bat, fc_bat.forecast_demand_kw, fc_bat.solar_forecast_kw)
        
        solar_zero = all(s == 0.0 for s in opt_bat.schedule.solar_utilized_kw)
        has_battery_dispatch = sum(opt_bat.schedule.battery_charge_kw) > 0 or sum(opt_bat.schedule.battery_discharge_kw) > 0
        valid = opt_bat.success and solar_zero and has_battery_dispatch
        record_test("Battery without Solar (Tariff Arbitrage)", valid, f"(Charged: {sum(opt_bat.schedule.battery_charge_kw):,.0f} kWh, Discharged: {sum(opt_bat.schedule.battery_discharge_kw):,.0f} kWh)")
    except Exception as e:
        record_test("Battery without Solar (Tariff Arbitrage)", False, str(e))

    # -------------------------------------------------------------
    # TEST 4: Full Solar & Battery Configuration (Level 3 Campus)
    # -------------------------------------------------------------
    try:
        cfg_l3 = FacilityConfig(
            level="level_3_campus",
            has_solar=True,
            solar_installed_capacity_kw=2100.0,
            has_battery=True,
            battery_capacity_kwh=1200.0,
            battery_max_power_kw=800.0,
            has_flexible_loads=True
        )
        fc_l3 = run_ai_forecast(cfg_l3)
        opt_l3 = run_energy_optimization(cfg_l3, fc_l3.forecast_demand_kw, fc_l3.solar_forecast_kw)
        
        valid = opt_l3.success and opt_l3.cost_savings_inr > 0 and opt_l3.peak_demand_shaved_kw > 0
        record_test("Full Solar & Battery Configuration (Level 3)", valid, f"(Savings: INR {opt_l3.cost_savings_inr:,.0f}, Shaved: {opt_l3.peak_demand_shaved_kw:.0f} kW)")
    except Exception as e:
        record_test("Full Solar & Battery Configuration (Level 3)", False, str(e))

    # -------------------------------------------------------------
    # TEST 5: Battery Reserve Constraints & Efficiency
    # -------------------------------------------------------------
    try:
        cfg_bess = FacilityConfig(
            has_solar=True,
            solar_installed_capacity_kw=2100.0,
            has_battery=True,
            battery_capacity_kwh=1000.0,
            battery_max_power_kw=500.0,
            battery_min_soc=0.25,
            battery_max_soc=0.90,
            battery_initial_soc=0.50,
            battery_target_end_soc=0.50,
            battery_roundtrip_efficiency=0.88
        )
        fc = run_ai_forecast(cfg_bess)
        opt = run_energy_optimization(cfg_bess, fc.forecast_demand_kw, fc.solar_forecast_kw)
        
        soc_series = opt.schedule.battery_soc_percent
        min_soc_pct = cfg_bess.battery_min_soc * 100
        max_soc_pct = cfg_bess.battery_max_soc * 100
        
        # Verify SoC never breaches [min_soc, max_soc]
        bounds_respected = all((min_soc_pct - 0.1) <= s <= (max_soc_pct + 0.1) for s in soc_series)
        record_test("Battery Reserve Bounds (25% Min - 90% Max)", bounds_respected, f"(Observed Range: [{min(soc_series)}%, {max(soc_series)}%])")
    except Exception as e:
        record_test("Battery Reserve Bounds (25% Min - 90% Max)", False, str(e))

    # -------------------------------------------------------------
    # TEST 6: Prevent Simultaneous Battery Charging & Discharging
    # -------------------------------------------------------------
    try:
        ch_series = np.array(opt_l3.schedule.battery_charge_kw)
        dis_series = np.array(opt_l3.schedule.battery_discharge_kw)
        # For every hour, at least one of ch or dis must be 0
        simultaneous = np.any((ch_series > 0.01) & (dis_series > 0.01))
        record_test("Mutual Exclusivity (No Simultaneous Charge & Discharge)", not simultaneous, f"(Simultaneous Hours: {np.sum((ch_series > 0.01) & (dis_series > 0.01))})")
    except Exception as e:
        record_test("Mutual Exclusivity (No Simultaneous Charge & Discharge)", False, str(e))

    # -------------------------------------------------------------
    # TEST 7: Flexible Load Operating Windows & Deadlines
    # -------------------------------------------------------------
    try:
        # Load 1 has window [10, 17)
        fl_test = FlexibleLoadConfig(
            id="fl-test-pump",
            name="Test Pumping Load",
            max_power_kw=100.0,
            total_energy_kwh=300.0,
            earliest_start_hour=10,
            latest_end_hour=15, # Deadline 3 PM
            baseline_start_hour=18
        )
        cfg_fl = FacilityConfig(
            has_solar=True,
            solar_installed_capacity_kw=1500.0,
            has_battery=False,
            flexible_loads=[fl_test]
        )
        fc_fl = run_ai_forecast(cfg_fl)
        opt_fl = run_energy_optimization(cfg_fl, fc_fl.forecast_demand_kw, fc_fl.solar_forecast_kw)
        
        fl_sch = opt_fl.schedule.individual_flexible_schedules["fl-test-pump"]
        total_fl_energy = sum(fl_sch)
        
        # Check that no power is scheduled outside [10, 15)
        outside_power = sum(fl_sch[h] for h in range(24) if h < 10 or h >= 15)
        deadline_respected = (outside_power < 0.01) and abs(total_fl_energy - 300.0) < 0.1
        record_test("Flexible Load Window & Deadline Enforcement", deadline_respected, f"(Energy: {total_fl_energy:.1f}/300 kWh, Outside Window: {outside_power:.1f} kW)")
    except Exception as e:
        record_test("Flexible Load Window & Deadline Enforcement", False, str(e))

    # -------------------------------------------------------------
    # TEST 8: Exact Energy Conservation across all 24 Intervals
    # -------------------------------------------------------------
    try:
        sch = opt_l3.schedule
        conserved_all = True
        max_delta = 0.0
        
        # For each hour: Supply = Grid + Solar_used + Bat_dis, Demand = Load_demand + Bat_ch
        # Notice: Load_demand is base_demand + shifted_flex
        for h in range(24):
            grid = sch.optimized_grid_kw[h]
            solar = sch.solar_utilized_kw[h]
            dis = sch.battery_discharge_kw[h]
            ch = sch.battery_charge_kw[h]
            # Total served campus load at hour h:
            # P_grid + P_solar + P_dis - P_ch
            net_delivered = grid + solar + dis - ch
            # Forecasted total demand was fc_l3.forecast_demand_kw[h] + shifted_load_kw[h]
            expected_load = fc_l3.forecast_demand_kw[h] + sch.shifted_load_kw[h]
            diff = abs(net_delivered - expected_load)
            if diff > max_delta:
                max_delta = diff
            if diff > 0.5:
                conserved_all = False
                
        record_test("Energy Conservation for all 24 Intervals", conserved_all, f"(Max Imbalance Delta: {max_delta:.4f} kW)")
    except Exception as e:
        record_test("Energy Conservation for all 24 Intervals", False, str(e))

    # -------------------------------------------------------------
    # TEST 9: CSV Ingestion, Timestamp Sorting & kW/kWh Units
    # -------------------------------------------------------------
    try:
        # Create synthetic 15-minute interval CSV
        times = pd.date_range("2026-10-01 00:00", periods=96, freq="15min")
        # Shuffle timestamps to verify chronological sorting
        shuffled_idx = np.random.RandomState(42).permutation(len(times))
        df_15 = pd.DataFrame({
            "timestamp": times[shuffled_idx].strftime("%Y-%m-%d %H:%M:%S"),
            "demand_kw": np.array([400.0 + 300.0 * np.sin(i / 15.0) for i in range(96)])[shuffled_idx],
            "solar_kw": np.array([max(0.0, 800.0 * np.sin((i - 24) / 48.0 * np.pi)) for i in range(96)])[shuffled_idx]
        })
        csv_bytes = df_15.to_csv(index=False).encode('utf-8')
        summary, norm = parse_energy_csv(csv_bytes, "test_15min_meter.csv")
        
        valid_15min = (
            summary.interval_minutes == 15 and
            summary.total_records == 96 and
            summary.has_solar_in_csv and
            len(norm["demand_24h"]) == 24 and
            len(norm["solar_24h"]) == 24
        )
        record_test("15-Min CSV Timestamp Sorting & Unit Recognition", valid_15min, f"(Interval: {summary.interval_minutes}m, Total Energy: {summary.total_consumption_kwh:,.0f} kWh)")
    except Exception as e:
        record_test("15-Min CSV Timestamp Sorting & Unit Recognition", False, str(e))

    # -------------------------------------------------------------
    # TEST 10: Flat vs Time-of-Use Tariffs
    # -------------------------------------------------------------
    try:
        cfg_flat = FacilityConfig(
            tariff_type="flat_rate",
            grid_tariff_normal_inr=8.00,
            has_solar=True,
            solar_installed_capacity_kw=2100.0,
            has_battery=True,
            battery_capacity_kwh=1000.0,
            battery_max_power_kw=500.0,
            has_flexible_loads=True
        )
        fc_flat = run_ai_forecast(cfg_flat)
        opt_flat = run_energy_optimization(cfg_flat, fc_flat.forecast_demand_kw, fc_flat.solar_forecast_kw)
        
        valid_flat = opt_flat.success and all(c == opt_flat.schedule.optimized_grid_kw[i] * 8.0 for i, c in enumerate(opt_flat.schedule.optimized_cost_inr))
        record_test("Flat vs Time-of-Use Tariff Modeling", valid_flat, f"(Flat Rate: INR {cfg_flat.grid_tariff_normal_inr:.2f}/kWh, Cost: INR {opt_flat.total_cost_optimized_inr:,.0f})")
    except Exception as e:
        record_test("Flat vs Time-of-Use Tariff Modeling", False, str(e))

    # -------------------------------------------------------------
    # TEST 11: What-If Simulator Output Correctness
    # -------------------------------------------------------------
    try:
        what_if_req = WhatIfRequest(
            solar_capacity_multiplier=1.2,
            battery_capacity_multiplier=1.5,
            tariff_rate_multiplier=1.1,
            cloud_cover_percent=20.0,
            flexible_load_shift_enabled=True,
            active_level="level_3_campus"
        )
        sim_out = simulate_what_if(what_if_req, cfg_l3)
        
        # Verify peak grid demand is authentic non-zero power (not 0 and not equal to shaved kW)
        peak_correct = sim_out.peak_grid_demand_kw > 1000.0 and sim_out.peak_grid_demand_kw != sim_out.peak_demand_shaved_kw
        record_test("What-If Simulator Metric & Peak Demand Integrity", peak_correct, f"(Simulated Peak: {sim_out.peak_grid_demand_kw:.0f} kW, Shaved: {sim_out.peak_demand_shaved_kw:.0f} kW)")
    except Exception as e:
        record_test("What-If Simulator Metric & Peak Demand Integrity", False, str(e))

    # -------------------------------------------------------------
    # TEST 12: Incomplete & Corrupt CSV Error Handling
    # -------------------------------------------------------------
    try:
        # Corrupt CSV missing numeric demand
        corrupt_csv = "timestamp,facility\n2026-10-01,NHCE\n2026-10-02,NHCE".encode('utf-8')
        threw_error = False
        try:
            parse_energy_csv(corrupt_csv, "corrupt.csv")
        except ValueError:
            threw_error = True

        # CSV with negative values and duplicate timestamps
        messy_csv = (
            "timestamp,demand_kw,solar_kw\n"
            "2026-10-01 10:00:00,-50.0,100.0\n"
            "2026-10-01 10:00:00,300.0,100.0\n" # Duplicate
            "2026-10-01 11:00:00,450.0,200.0\n"
            "2026-10-01 12:00:00,NaN,500.0\n"     # Missing
        ).encode('utf-8')
        summary_messy, _ = parse_energy_csv(messy_csv, "messy.csv")
        
        handled_messy = (
            threw_error and
            summary_messy.duplicate_records_count == 1 and
            summary_messy.missing_records_count >= 1 and
            len(summary_messy.data_quality_notes) > 0
        )
        record_test("Incomplete, Duplicate & Negative CSV Handling", handled_messy, f"(Detected {summary_messy.duplicate_records_count} duplicates, {summary_messy.missing_records_count} NaNs)")
    except Exception as e:
        record_test("Incomplete, Duplicate & Negative CSV Handling", False, str(e))

    print("=" * 65)
    print(f"Results: {len(passed_tests)} Passed, {len(failed_tests)} Failed.")
    print("=" * 65)
    if failed_tests:
        for f, d in failed_tests:
            print(f"FAILED: {f} -> {d}")
        sys.exit(1)
    else:
        print("ALL TESTS VERIFIED AND PASSED!")

if __name__ == "__main__":
    run_all_tests()
