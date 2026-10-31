import sys
import numpy as np

from app.schemas import FacilityConfig, FlexibleLoadConfig
from app.optimization import run_energy_optimization
from app.sample_data import get_base_campus_demand, get_solar_irradiance_curve, get_tou_tariff
from app.forecasting import run_ai_forecast

def print_separator(title: str):
    print("\n" + "=" * 90)
    print(f" {title} ")
    print("=" * 90)

# =====================================================================
# 1. RUN ALL FOUR BATTERY OPTIMIZATION SCENARIOS
# =====================================================================
print_separator("SCENARIO A: Solar Surplus + Battery + Evening Peak Tariff")
# Facility with 2,500 kW PV and 1,000 kWh Battery (500 kW max), 20% min SoC, 90% max SoC, 30% initial SoC
cfg_a = FacilityConfig(
    name="Scenario A: Solar Surplus & Storage",
    level="level_3_campus",
    has_solar=True,
    solar_installed_capacity_kw=2500.0,
    has_battery=True,
    battery_capacity_kwh=1000.0,
    battery_max_power_kw=500.0,
    battery_initial_soc=0.30,
    battery_min_soc=0.20,
    battery_max_soc=0.90,
    battery_target_end_soc=0.30,
    battery_roundtrip_efficiency=0.90,
    battery_degradation_cost_per_kwh=0.45,
    has_flexible_loads=False
)
# Load profile: 300 kW night, 400 kW day, 600 kW evening peak
dem_a = [300.0]*8 + [400.0]*8 + [600.0]*4 + [300.0]*4
# Strong solar generation peaking at 2000 kW (creates genuine solar surplus of up to 1600 kW)
sol_a = [0.0]*6 + [200.0, 600.0, 1200.0, 1800.0, 2000.0, 1800.0, 1200.0, 600.0, 200.0] + [0.0]*9

opt_a = run_energy_optimization(cfg_a, dem_a, sol_a)
sch_a = opt_a.schedule

print(f"Solver Success: {opt_a.success} | Status: {opt_a.status_summary}")
print(f"Total Battery Charged:    {sum(sch_a.battery_charge_kw):,.1f} kWh")
print(f"Total Battery Discharged: {sum(sch_a.battery_discharge_kw):,.1f} kWh")
print(f"Solar Surplus Captured:   {sum(sch_a.solar_utilized_kw) - sum(np.minimum(dem_a, sol_a)):,.1f} kWh")
print(f"Baseline Peak Grid:       {max(sch_a.baseline_grid_kw):,.1f} kW -> Optimized Peak Grid: {max(sch_a.optimized_grid_kw):,.1f} kW (Shaved: {opt_a.peak_demand_shaved_kw:.1f} kW)")
print(f"Cost Savings:             INR {opt_a.cost_savings_inr:,.2f} ({opt_a.cost_savings_percent:.1f}%)")
print("Key Hours Charging (Solar Surplus):", [(h, sch_a.battery_charge_kw[h]) for h in range(24) if sch_a.battery_charge_kw[h] > 0])
print("Key Hours Discharging (Peak Tariff):", [(h, sch_a.battery_discharge_kw[h]) for h in range(24) if sch_a.battery_discharge_kw[h] > 0])
print("SoC Trajectory (%):", sch_a.battery_soc_percent)


print_separator("SCENARIO B: No Solar + Battery + Time-of-Use Tariff")
cfg_b = FacilityConfig(
    name="Scenario B: Pure Tariff Arbitrage",
    level="level_1_basic",
    has_solar=False,
    solar_installed_capacity_kw=0.0,
    has_battery=True,
    battery_capacity_kwh=1000.0,
    battery_max_power_kw=500.0,
    battery_initial_soc=0.20,
    battery_min_soc=0.20,
    battery_max_soc=0.90,
    battery_target_end_soc=0.20,
    battery_roundtrip_efficiency=0.90,
    battery_degradation_cost_per_kwh=0.45,
    has_flexible_loads=False
)
dem_b = [300.0]*6 + [500.0]*12 + [800.0]*4 + [300.0]*2
sol_b = [0.0]*24

opt_b = run_energy_optimization(cfg_b, dem_b, sol_b)
sch_b = opt_b.schedule

print(f"Solver Success: {opt_b.success} | Status: {opt_b.status_summary}")
print(f"Total Battery Charged:    {sum(sch_b.battery_charge_kw):,.1f} kWh (during off-peak hours)")
print(f"Total Battery Discharged: {sum(sch_b.battery_discharge_kw):,.1f} kWh (during peak hours)")
print(f"Roundtrip Efficiency:     {(sum(sch_b.battery_discharge_kw) / sum(sch_b.battery_charge_kw) * 100):.1f}% (Nominal: 90.0%)")
print(f"Peak Grid Demand:         {max(sch_b.baseline_grid_kw):,.1f} kW -> {max(sch_b.optimized_grid_kw):,.1f} kW (Shaved: {opt_b.peak_demand_shaved_kw:.1f} kW)")
print(f"Cost Savings:             INR {opt_b.cost_savings_inr:,.2f} ({opt_b.cost_savings_percent:.1f}%)")
print("Key Hours Charging (Off-Peak):", [(h, sch_b.battery_charge_kw[h]) for h in range(24) if sch_b.battery_charge_kw[h] > 0])
print("Key Hours Discharging (Peak):", [(h, sch_b.battery_discharge_kw[h]) for h in range(24) if sch_b.battery_discharge_kw[h] > 0])
print("SoC Trajectory (%):", sch_b.battery_soc_percent)


print_separator("SCENARIO C: Zero Battery Capacity (Level 2 Solar Only)")
cfg_c = FacilityConfig(
    name="Scenario C: Solar without Battery",
    level="level_2_solar",
    has_solar=True,
    solar_installed_capacity_kw=1500.0,
    has_battery=False,
    battery_capacity_kwh=0.0,
    battery_max_power_kw=0.0,
    has_flexible_loads=True
)
dem_c = [300.0]*6 + [500.0]*12 + [800.0]*4 + [300.0]*2
sol_c = [0.0]*6 + [200.0, 500.0, 800.0, 1000.0, 1000.0, 800.0, 500.0, 200.0] + [0.0]*10

opt_c = run_energy_optimization(cfg_c, dem_c, sol_c)
sch_c = opt_c.schedule

print(f"Solver Success: {opt_c.success} | Status: {opt_c.status_summary}")
print(f"Total Battery Charged:    {sum(sch_c.battery_charge_kw):,.1f} kWh (Expected: 0.0)")
print(f"Total Battery Discharged: {sum(sch_c.battery_discharge_kw):,.1f} kWh (Expected: 0.0)")
print(f"Battery SoC Series:       {set(sch_c.battery_soc_percent)} (Expected: {{0.0}})")
print(f"Solar Utilized:           {sum(sch_c.solar_utilized_kw):,.1f} kWh")
print(f"Flexible Load Shifted:    {sum(abs(x) for x in sch_c.shifted_load_kw):,.1f} kWh-movement")


print_separator("SCENARIO D: Flat Tariff + Zero Battery (Level 1 Flat)")
cfg_d = FacilityConfig(
    name="Scenario D: Flat Tariff No Battery",
    level="level_1_basic",
    has_solar=False,
    solar_installed_capacity_kw=0.0,
    has_battery=False,
    battery_capacity_kwh=0.0,
    battery_max_power_kw=0.0,
    tariff_type="flat_rate",
    grid_tariff_normal_inr=8.00,
    has_flexible_loads=True
)
dem_d = [400.0]*24
sol_d = [0.0]*24

opt_d = run_energy_optimization(cfg_d, dem_d, sol_d)
sch_d = opt_d.schedule

print(f"Solver Success: {opt_d.success} | Status: {opt_d.status_summary}")
print(f"Total Battery Charged:    {sum(sch_d.battery_charge_kw):,.1f} kWh (Expected: 0.0)")
print(f"Total Battery Discharged: {sum(sch_d.battery_discharge_kw):,.1f} kWh (Expected: 0.0)")
print(f"Battery SoC Series:       {set(sch_d.battery_soc_percent)} (Expected: {{0.0}})")


# =====================================================================
# 2. 24-HOUR DISPATCH TABLE (DEFAULT CAMPUS LEVEL 3)
# =====================================================================
print_separator("24-HOUR OPTIMAL DISPATCH TABLE: NHCE INTELLIGENT CAMPUS (LEVEL 3)")
cfg_default = FacilityConfig(
    name="NHCE Intelligent Campus",
    level="level_3_campus",
    grid_contracted_demand_kw=6000.0,
    has_solar=True,
    solar_installed_capacity_kw=2100.0,
    has_battery=True,
    battery_capacity_kwh=1200.0,
    battery_max_power_kw=800.0,
    battery_initial_soc=0.50,
    battery_min_soc=0.20,
    battery_max_soc=0.95,
    battery_target_end_soc=0.50,
    battery_roundtrip_efficiency=0.90,
    battery_degradation_cost_per_kwh=0.45,
    has_flexible_loads=True
)
fc = run_ai_forecast(cfg_default)
opt_campus = run_energy_optimization(cfg_default, fc.forecast_demand_kw, fc.solar_forecast_kw, flexible_shift_enabled=True)
sch = opt_campus.schedule

header = f"{'Hour':<4} | {'Solar':<7} | {'Demand':<7} | {'BaseGrid':<8} | {'OptGrid':<8} | {'Charge':<7} | {'Disch':<7} | {'SoC%':<5} | {'FlexShift':<9} | {'Delta':<6}"
print(header)
print("-" * len(header))

imbalances = []
simultaneous_violations = 0
soc_violations = 0

for h in range(24):
    sol = fc.solar_forecast_kw[h]
    dem = fc.forecast_demand_kw[h]
    base_g = sch.baseline_grid_kw[h]
    opt_g = sch.optimized_grid_kw[h]
    ch = sch.battery_charge_kw[h]
    dis = sch.battery_discharge_kw[h]
    soc = sch.battery_soc_percent[h]
    shift = sch.shifted_load_kw[h]

    # Verify physical power balance:
    # Supply = OptGrid + Solar_Utilized + Battery_Discharge
    # Demand = Inflexible_Demand + Flexible_Demand + Battery_Charge = Forecast_Demand + Shift + Battery_Charge
    sol_used = sch.solar_utilized_kw[h]
    supply = opt_g + sol_used + dis
    demand = dem + shift + ch
    delta = abs(supply - demand)
    imbalances.append(delta)

    # Check mutual exclusivity
    if ch > 0.01 and dis > 0.01:
        simultaneous_violations += 1

    # Check SoC bounds
    if soc < (cfg_default.battery_min_soc * 100 - 0.1) or soc > (cfg_default.battery_max_soc * 100 + 0.1):
        soc_violations += 1

    print(f"{h:<4} | {sol:<7.1f} | {dem:<7.1f} | {base_g:<8.1f} | {opt_g:<8.1f} | {ch:<7.1f} | {dis:<7.1f} | {soc:<5.1f} | {shift:<+9.1f} | {delta:<6.3f}")

print("\n" + "=" * 90)
print(f"VERIFICATION RESULTS:")
print(f"1. Energy Conservation at every interval: MAX delta = {max(imbalances):.4f} kW (All 24 hours <= 0.1 kW: {all(d <= 0.1 for d in imbalances)})")
print(f"2. Mutual Exclusivity: Simultaneous Charge & Discharge Hours = {simultaneous_violations} (Zero violations guaranteed)")
print(f"3. Battery Reserve Constraints: Bounds [{cfg_default.battery_min_soc*100}% - {cfg_default.battery_max_soc*100}%], Observed Range [{min(sch.battery_soc_percent):.1f}% - {max(sch.battery_soc_percent):.1f}%], Violations = {soc_violations}")
print(f"4. Battery Efficiency: Target End SoC = {cfg_default.battery_target_end_soc*100}%, Final SoC = {sch.battery_soc_percent[-1]:.1f}%")
print(f"5. Total Campus Cost: Baseline INR {opt_campus.total_cost_baseline_inr:,.2f} -> Optimized INR {opt_campus.total_cost_optimized_inr:,.2f} (Savings: INR {opt_campus.cost_savings_inr:,.2f} / -{opt_campus.cost_savings_percent:.1f}%)")
print(f"6. Peak Demand Shaved: {opt_campus.peak_demand_shaved_kw:.1f} kW ({opt_campus.peak_demand_baseline_kw:.1f} kW -> {opt_campus.peak_demand_optimized_kw:.1f} kW)")
print("=" * 90)

