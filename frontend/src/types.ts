export type DeploymentLevel = 'level_1_basic' | 'level_2_solar' | 'level_3_campus';

export interface BuildingLoad {
  id: string;
  name: string;
  category: string;
  current_load_kw: number;
  base_load_kw: number;
  peak_load_kw: number;
  is_flexible: boolean;
  flexible_capacity_kw: number;
  operational_status: string;
  temperature_c?: number;
  occupancy_percent: number;
}

export interface FlexibleLoadConfig {
  id: string;
  name: string;
  max_power_kw: number;
  total_energy_kwh: number;
  earliest_start_hour: number;
  latest_end_hour: number;
  baseline_start_hour: number;
}

export interface FacilityConfig {
  name: string;
  level: DeploymentLevel;
  grid_contracted_demand_kw: number;
  has_solar: boolean;
  solar_installed_capacity_kw: number;
  has_battery: boolean;
  battery_capacity_kwh: number;
  battery_max_power_kw: number;
  battery_min_soc: number;
  battery_max_soc: number;
  battery_initial_soc?: number;
  battery_target_end_soc?: number;
  battery_roundtrip_efficiency: number;
  battery_degradation_cost_per_kwh: number;
  has_flexible_loads: boolean;
  flexible_loads?: FlexibleLoadConfig[];
  tariff_type: string;
  grid_tariff_peak_inr: number;
  grid_tariff_normal_inr: number;
  grid_tariff_offpeak_inr: number;
  grid_demand_charge_per_kw_month_inr?: number;
  grid_co2_factor_kg_kwh: number;
}

export interface EnergyFlowState {
  timestamp: string;
  solar_generation_kw: number;
  solar_capacity_kw: number;
  grid_consumption_kw: number;
  grid_import_kw: number;
  grid_export_kw: number;
  battery_flow_kw: number;
  battery_soc_percent: number;
  battery_capacity_kwh: number;
  campus_demand_kw: number;
  power_balance_verified: boolean;
  balance_delta_kw: number;
  data_fidelity: string;
}

export interface AnomalyItem {
  id: string;
  timestamp: string;
  hour: number;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  anomaly_type: string;
  excess_kwh: number;
  estimated_waste_cost_inr: number;
  recommended_action: string;
}

export interface ForecastResponse {
  deployment_level: DeploymentLevel;
  weather_summary: {
    condition: string;
    peak_irradiance_w_m2: number;
    avg_temperature_c: number;
    max_temperature_c: number;
    cloud_cover_percent: number;
    cooling_degree_impact_percent: number;
    data_source?: string;
  };
  hours: number[];
  time_labels: string[];
  actual_demand_kw: number[];
  forecast_demand_kw: number[];
  demand_upper_bound_kw: number[];
  demand_lower_bound_kw: number[];
  solar_forecast_kw: number[];
  solar_upper_bound_kw: number[];
  solar_lower_bound_kw: number[];
  anomalies: AnomalyItem[];
  model_metadata: {
    demand_algorithm: string;
    solar_algorithm: string;
    r2_score_demand: number;
    mae_kw: number;
    rmse_kw?: number;
    training_samples?: number;
    test_samples_evaluated?: number;
    model_validation?: string;
  };
}

export interface OptimizationRecommendation {
  id: string;
  title: string;
  category: string;
  priority: 'high' | 'medium' | 'low';
  reasoning: string;
  energy_impact: string;
  financial_impact_inr: number;
  operational_constraints: string;
  implemented: boolean;
}

export interface MetricComparison {
  metric_name: string;
  unit: string;
  baseline_value: number;
  optimized_value: number;
  change_value: number;
  change_percent: number;
  is_positive: boolean;
}

export interface OptimizationSchedule {
  hours: number[];
  time_labels: string[];
  baseline_grid_kw: number[];
  optimized_grid_kw: number[];
  baseline_cost_inr: number[];
  optimized_cost_inr: number[];
  solar_utilized_kw: number[];
  solar_curtailed_kw: number[];
  battery_charge_kw: number[];
  battery_discharge_kw: number[];
  battery_soc_percent: number[];
  shifted_load_kw: number[];
  solar_surplus_kw?: number[];
  individual_flexible_schedules?: Record<string, number[]>;
}

export interface OptimizationResponse {
  success: boolean;
  deployment_level: DeploymentLevel;
  status_summary: string;
  schedule: OptimizationSchedule;
  metrics_summary: MetricComparison[];
  total_cost_baseline_inr: number;
  total_cost_optimized_inr: number;
  baseline_energy_cost_inr: number;
  baseline_demand_charge_inr: number;
  optimized_energy_cost_inr: number;
  optimized_demand_charge_inr: number;
  battery_degradation_cost_inr: number;
  cost_savings_inr: number;
  cost_savings_percent: number;
  grid_reduction_kwh: number;
  co2_avoided_tons: number;
  peak_demand_baseline_kw: number;
  peak_demand_optimized_kw: number;
  peak_demand_shaved_kw: number;
  recommendations: OptimizationRecommendation[];
  computation_time_ms: number;
  power_balance_max_error_kw?: number;
}

export interface LiveDashboardResponse {
  facility_name: string;
  deployment_level: DeploymentLevel;
  kpis: {
    total_consumption_kwh: number;
    total_consumption_trend: string;
    solar_generation_kwh: number;
    solar_generation_trend: string;
    battery_soc_percent: number;
    battery_status: string;
    grid_consumption_kwh: number;
    grid_consumption_trend: string;
    estimated_cost_today_inr: number;
    estimated_cost_trend: string;
    co2_emissions_avoided_tons: number;
    co2_trend: string;
  };
  energy_flow: EnergyFlowState;
  active_recommendation?: OptimizationRecommendation;
  total_anomalies_detected: number;
  data_fidelity_badges: {
    historical_data: string;
    ai_models: string;
    hardware_automation: string;
  };
}

export interface WhatIfRequest {
  solar_capacity_multiplier: number;
  battery_capacity_multiplier: number;
  tariff_rate_multiplier: number;
  cloud_cover_percent: number;
  flexible_load_shift_enabled: boolean;
  active_level: DeploymentLevel;
}

export interface WhatIfResponse {
  inputs: WhatIfRequest;
  baseline_cost_inr: number;
  simulated_cost_inr: number;
  savings_inr: number;
  savings_percent: number;
  grid_consumption_kwh: number;
  solar_generation_kwh: number;
  solar_self_consumption_percent: number;
  co2_emissions_tons: number;
  co2_avoided_tons: number;
  peak_grid_demand_kw: number;
  peak_demand_shaved_kw?: number;
  explanation: string;
}

export interface CSVUploadSummary {
  filename: string;
  detected_format: string;
  total_records: number;
  date_range: string;
  interval_minutes?: number;
  total_consumption_kwh: number;
  peak_recorded_demand_kw: number;
  has_solar_in_csv: boolean;
  total_solar_kwh: number;
  estimated_bill_inr: number;
  identified_wastage_kwh: number;
  identified_savings_potential_inr: number;
  inferred_level: DeploymentLevel;
  data_quality_notes?: string[];
  missing_records_count?: number;
  duplicate_records_count?: number;
  recommendation_summary: string;
}
