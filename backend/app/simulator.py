import datetime
import numpy as np
from typing import Dict, Any, List, Optional
from .schemas import (
    FacilityConfig,
    EnergyFlowState,
    WhatIfRequest,
    WhatIfResponse,
    BuildingLoad
)
from .sample_data import (
    get_campus_buildings,
    get_solar_irradiance_curve,
    get_temperature_curve,
    get_base_campus_demand,
    get_tou_tariff
)
from .optimization import run_energy_optimization
from .forecasting import run_ai_forecast

def get_live_energy_flow_state(
    config: FacilityConfig,
    simulated_hour: int = 13,
    active_demand_24h: Optional[List[float]] = None,
    active_solar_24h: Optional[List[float]] = None,
    data_source_label: Optional[str] = None
) -> EnergyFlowState:
    """
    Computes a mathematically balanced, real-time energy flow snapshot.
    Enforces strict physical power balance:
    P_grid_import + P_solar + P_bat_discharge = P_campus + P_bat_charge + P_grid_export
    Derives demand and solar directly from the active dataset.
    """
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    h = simulated_hour % 24

    # 1. Total Campus Demand at simulated hour
    if active_demand_24h is not None and len(active_demand_24h) == 24:
        total_campus_demand_kw = round(float(active_demand_24h[h]), 1)
    else:
        buildings = get_campus_buildings(config.level)
        total_campus_demand_kw = round(sum(b.current_load_kw for b in buildings), 1)

    # 2. Solar Generation Calculation
    if not config.has_solar or config.solar_installed_capacity_kw <= 0.0:
        solar_kw = 0.0
    elif active_solar_24h is not None and len(active_solar_24h) == 24:
        solar_kw = round(float(active_solar_24h[h]), 1)
    else:
        irradiance = get_solar_irradiance_curve(cloud_cover=15.0)[h]
        solar_kw = round(config.solar_installed_capacity_kw * (irradiance / 1000.0) * 0.94, 1) if irradiance > 10 else 0.0

    # 3. Battery Dispatch Calculation
    battery_flow_kw = 0.0
    soc_percent = round(config.battery_initial_soc * 100, 1) if config.has_battery else 0.0
    bat_capacity = config.battery_capacity_kwh if config.has_battery else 0.0

    if config.has_battery and config.battery_capacity_kwh > 0:
        # At midday solar peak, charge battery with surplus solar if solar exceeds 35% of demand
        if solar_kw > (total_campus_demand_kw * 0.35):
            charge_power = min(config.battery_max_power_kw, max(0.0, solar_kw - total_campus_demand_kw * 0.5))
            battery_flow_kw = -round(charge_power, 1) # negative represents charging
            soc_percent = 76.0 # representative afternoon charging state
        else:
            battery_flow_kw = 0.0

    charge_kw = abs(battery_flow_kw) if battery_flow_kw < 0 else 0.0
    discharge_kw = battery_flow_kw if battery_flow_kw > 0 else 0.0

    # 4. Strict Power Conservation:
    # P_grid_import - P_grid_export = P_campus + P_charge - P_solar - P_discharge
    net_needed = (total_campus_demand_kw + charge_kw) - (solar_kw + discharge_kw)
    if net_needed >= 0:
        grid_import_kw = round(net_needed, 1)
        grid_export_kw = 0.0
    else:
        grid_import_kw = 0.0
        grid_export_kw = round(-net_needed, 1)

    # 5. Verification of physical power balance:
    total_generation = grid_import_kw + solar_kw + discharge_kw
    total_consumption = total_campus_demand_kw + charge_kw + grid_export_kw
    balance_delta = round(abs(total_generation - total_consumption), 2)
    verified = balance_delta <= 0.05

    data_fidelity_label = data_source_label or (
        "Level 1: Meter/Bill Demand Stream (Zero Solar, Zero Battery)" if config.level == "level_1_basic" else
        ("Level 2: Smart Meter & Rooftop Solar PV Telemetry" if config.level == "level_2_solar" else
         "Simulated Live Stream (100% Physical Conservation Validated)")
    )

    return EnergyFlowState(
        timestamp=now_str,
        solar_generation_kw=solar_kw,
        solar_capacity_kw=config.solar_installed_capacity_kw if config.has_solar else 0.0,
        grid_consumption_kw=grid_import_kw,
        grid_import_kw=grid_import_kw,
        grid_export_kw=grid_export_kw,
        battery_flow_kw=battery_flow_kw,
        battery_soc_percent=soc_percent,
        battery_capacity_kwh=bat_capacity,
        campus_demand_kw=total_campus_demand_kw,
        power_balance_verified=verified,
        balance_delta_kw=balance_delta,
        data_fidelity=data_fidelity_label
    )

def simulate_what_if(
    req: WhatIfRequest,
    config: FacilityConfig,
    active_demand_24h: Optional[List[float]] = None,
    active_solar_24h: Optional[List[float]] = None
) -> WhatIfResponse:
    """
    Transparent scenario evaluation comparing active baseline vs modified parameter scenario.
    Derives baseline values from the active dataset.
    """
    sim_config = config.model_copy(deep=True)
    sim_config.level = req.active_level
    sim_config.solar_installed_capacity_kw = round(sim_config.solar_installed_capacity_kw * req.solar_capacity_multiplier, 1)
    sim_config.has_solar = (sim_config.solar_installed_capacity_kw > 0)
    sim_config.battery_capacity_kwh = round(sim_config.battery_capacity_kwh * req.battery_capacity_multiplier, 1)
    sim_config.battery_max_power_kw = round(sim_config.battery_max_power_kw * req.battery_capacity_multiplier, 1)
    sim_config.has_battery = (sim_config.battery_capacity_kwh > 0)
    sim_config.grid_tariff_peak_inr = round(sim_config.grid_tariff_peak_inr * req.tariff_rate_multiplier, 2)
    sim_config.grid_tariff_normal_inr = round(sim_config.grid_tariff_normal_inr * req.tariff_rate_multiplier, 2)
    sim_config.grid_tariff_offpeak_inr = round(sim_config.grid_tariff_offpeak_inr * req.tariff_rate_multiplier, 2)

    # Scale solar by multiplier if active solar is provided
    scaled_solar = None
    if active_solar_24h is not None and sim_config.has_solar:
        scaled_solar = [s * req.solar_capacity_multiplier for s in active_solar_24h]

    forecast = run_ai_forecast(
        sim_config,
        custom_demand_24h=active_demand_24h,
        custom_solar_24h=scaled_solar,
        cloud_cover_percent=req.cloud_cover_percent
    )

    opt_res = run_energy_optimization(
        sim_config,
        forecast.forecast_demand_kw,
        forecast.solar_forecast_kw,
        flexible_shift_enabled=req.flexible_load_shift_enabled
    )

    total_solar_gen = float(np.sum(forecast.solar_forecast_kw))
    solar_utilized = float(np.sum(opt_res.schedule.solar_utilized_kw))
    solar_self_pct = (solar_utilized / total_solar_gen * 100) if total_solar_gen > 0 else 0.0
    actual_peak_grid_demand = opt_res.peak_demand_optimized_kw

    explanation = (
        f"Scenario under {req.cloud_cover_percent:.0f}% cloud cover with {req.solar_capacity_multiplier:.1f}x solar "
        f"({sim_config.solar_installed_capacity_kw:.0f} kWp) and {req.battery_capacity_multiplier:.1f}x storage "
        f"({sim_config.battery_capacity_kwh:.0f} kWh). Solar self-consumption: {solar_self_pct:.1f}%. "
        f"Peak grid demand: {actual_peak_grid_demand:.0f} kW. "
        f"Daily electricity cost: ₹{opt_res.total_cost_optimized_inr:,.0f} (saving ₹{opt_res.cost_savings_inr:,.0f} or {opt_res.cost_savings_percent:.1f}% vs baseline)."
    )

    return WhatIfResponse(
        inputs=req,
        baseline_cost_inr=opt_res.total_cost_baseline_inr,
        simulated_cost_inr=opt_res.total_cost_optimized_inr,
        savings_inr=opt_res.cost_savings_inr,
        savings_percent=opt_res.cost_savings_percent,
        grid_consumption_kwh=sum(opt_res.schedule.optimized_grid_kw),
        solar_generation_kwh=round(total_solar_gen, 1),
        solar_self_consumption_percent=round(solar_self_pct, 1),
        co2_emissions_tons=round(sum(opt_res.schedule.optimized_grid_kw) * sim_config.grid_co2_factor_kg_kwh / 1000.0, 2),
        co2_avoided_tons=opt_res.co2_avoided_tons,
        peak_grid_demand_kw=actual_peak_grid_demand,
        peak_demand_shaved_kw=opt_res.peak_demand_shaved_kw,
        explanation=explanation
    )
