from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, model_validator

DeploymentLevel = Literal["level_1_basic", "level_2_solar", "level_3_campus"]
TariffType = Literal["time_of_use", "flat_rate", "tiered"]

class BuildingLoad(BaseModel):
    id: str
    name: str
    category: str # "Academic", "Laboratories", "Hostel & Dining", "Auditorium & Library", "Utilities & Pumps"
    current_load_kw: float = Field(ge=0.0)
    base_load_kw: float = Field(ge=0.0)
    peak_load_kw: float = Field(ge=0.0)
    is_flexible: bool = False
    flexible_capacity_kw: float = Field(default=0.0, ge=0.0)
    operational_status: str # "Normal", "High Demand", "Optimized", "Idle"
    temperature_c: Optional[float] = None
    occupancy_percent: int = Field(ge=0, le=100)

class FlexibleLoadConfig(BaseModel):
    id: str
    name: str
    max_power_kw: float = Field(gt=0.0)
    total_energy_kwh: float = Field(gt=0.0)
    earliest_start_hour: int = Field(ge=0, le=23)
    latest_end_hour: int = Field(ge=1, le=24) # Deadline hour
    baseline_start_hour: int = Field(ge=0, le=23) # where load runs uncoordinated

    @model_validator(mode='after')
    def validate_hours(self):
        if self.latest_end_hour <= self.earliest_start_hour:
            raise ValueError(f"latest_end_hour ({self.latest_end_hour}) must be > earliest_start_hour ({self.earliest_start_hour})")
        avail_hours = self.latest_end_hour - self.earliest_start_hour
        if avail_hours * self.max_power_kw < self.total_energy_kwh - 1e-4:
            raise ValueError(f"Flexible load {self.name}: energy required {self.total_energy_kwh} kWh exceeds maximum capacity {avail_hours * self.max_power_kw} kWh in allowed window [{self.earliest_start_hour}, {self.latest_end_hour}]")
        return self

def get_default_flexible_loads() -> List[FlexibleLoadConfig]:
    return [
        FlexibleLoadConfig(
            id="flex-water-pump",
            name="Raw Water Treatment & Pumping",
            max_power_kw=150.0,
            total_energy_kwh=450.0,
            earliest_start_hour=10,
            latest_end_hour=17, # Deadline 5 PM (overhead tanks must be full before hostel rush)
            baseline_start_hour=18 # Uncoordinated baseline runs during 6-9 PM peak
        ),
        FlexibleLoadConfig(
            id="flex-chiller-pre-cool",
            name="HVAC Thermal Storage & Pre-Cooling",
            max_power_kw=250.0,
            total_energy_kwh=750.0,
            earliest_start_hour=11,
            latest_end_hour=16, # Deadline 4 PM (precool building before afternoon/evening)
            baseline_start_hour=17 # Uncoordinated baseline starts late afternoon
        ),
        FlexibleLoadConfig(
            id="flex-ev-fleet",
            name="Campus Shuttle & EV Charging Hub",
            max_power_kw=120.0,
            total_energy_kwh=360.0,
            earliest_start_hour=11,
            latest_end_hour=16, # Deadline 4 PM (fleet charged before evening runs)
            baseline_start_hour=19 # Uncoordinated baseline plugs in during 7-10 PM peak
        )
    ]

class FacilityConfig(BaseModel):
    name: str = "NHCE Green Campus"
    level: DeploymentLevel = "level_3_campus"
    grid_contracted_demand_kw: float = Field(default=6000.0, gt=0.0)
    has_solar: bool = True
    solar_installed_capacity_kw: float = Field(default=2100.0, ge=0.0)
    has_battery: bool = True
    battery_capacity_kwh: float = Field(default=1200.0, ge=0.0)
    battery_max_power_kw: float = Field(default=800.0, ge=0.0)
    battery_min_soc: float = Field(default=0.20, ge=0.0, le=1.0)  # 20% reserve
    battery_max_soc: float = Field(default=0.95, ge=0.0, le=1.0)  # 95% protection
    battery_initial_soc: float = Field(default=0.50, ge=0.0, le=1.0) # 50% start of day
    battery_target_end_soc: float = Field(default=0.50, ge=0.0, le=1.0) # neutral daily cycle
    battery_roundtrip_efficiency: float = Field(default=0.90, gt=0.0, le=1.0)
    battery_degradation_cost_per_kwh: float = Field(default=0.45, ge=0.0)  # ₹ / kWh throughput
    has_flexible_loads: bool = True
    flexible_loads: List[FlexibleLoadConfig] = Field(default_factory=get_default_flexible_loads)
    tariff_type: TariffType = "time_of_use"
    grid_tariff_peak_inr: float = Field(default=11.50, ge=0.0)     # ₹ / kWh (6 PM - 10 PM)
    grid_tariff_normal_inr: float = Field(default=7.50, ge=0.0)   # ₹ / kWh (6 AM - 6 PM, 10 PM - 11 PM)
    grid_tariff_offpeak_inr: float = Field(default=4.80, ge=0.0)  # ₹ / kWh (11 PM - 6 AM)
    grid_demand_charge_per_kw_month_inr: float = Field(default=280.0, ge=0.0) # ₹/kVA-month
    grid_co2_factor_kg_kwh: float = Field(default=0.72, ge=0.0)   # Indian CEA standard grid emission factor (~0.72 kg CO2 / kWh)

    @model_validator(mode='after')
    def validate_battery_soc(self):
        if self.battery_min_soc >= self.battery_max_soc:
            raise ValueError(f"battery_min_soc ({self.battery_min_soc}) must be strictly less than battery_max_soc ({self.battery_max_soc})")
        if not (self.battery_min_soc <= self.battery_initial_soc <= self.battery_max_soc):
            raise ValueError(f"battery_initial_soc ({self.battery_initial_soc}) must be between min ({self.battery_min_soc}) and max ({self.battery_max_soc})")
        return self

class HourlyDataPoint(BaseModel):
    hour: int
    time_label: str
    demand_kw: float
    solar_kw: float
    grid_kw: float
    battery_charge_kw: float
    battery_discharge_kw: float
    battery_soc_percent: float
    tariff_inr: float
    cost_inr: float
    co2_kg: float

class EnergyFlowState(BaseModel):
    timestamp: str
    solar_generation_kw: float
    solar_capacity_kw: float
    grid_consumption_kw: float
    grid_import_kw: float
    grid_export_kw: float
    battery_flow_kw: float # positive: discharge, negative: charge
    battery_soc_percent: float
    battery_capacity_kwh: float
    campus_demand_kw: float
    power_balance_verified: bool
    balance_delta_kw: float
    data_fidelity: str

class AnomalyItem(BaseModel):
    id: str
    timestamp: str
    hour: int
    title: str
    description: str
    severity: Literal["low", "medium", "high"]
    anomaly_type: str # "Vampire Baseload", "Peak Exceedance", "Solar Underperformance", "HVAC Inefficiency"
    excess_kwh: float
    estimated_waste_cost_inr: float
    recommended_action: str

class ForecastResponse(BaseModel):
    deployment_level: DeploymentLevel
    weather_summary: Dict[str, Any]
    hours: List[int]
    time_labels: List[str]
    actual_demand_kw: List[float]
    forecast_demand_kw: List[float]
    demand_upper_bound_kw: List[float]
    demand_lower_bound_kw: List[float]
    solar_forecast_kw: List[float]
    solar_upper_bound_kw: List[float]
    solar_lower_bound_kw: List[float]
    anomalies: List[AnomalyItem]
    model_metadata: Dict[str, Any]

class OptimizationRecommendation(BaseModel):
    id: str
    title: str
    category: str # "Flexible Load Shift", "Battery Dispatch", "Peak Shaving", "Solar Self-Consumption"
    priority: Literal["high", "medium", "low"]
    reasoning: str
    energy_impact: str # e.g. "Shifted 600 kWh from evening peak to 12-3 PM solar surplus"
    financial_impact_inr: float
    operational_constraints: str # e.g. "Water tanks filled before 17:00; ±1.2°C temperature band respected"
    implemented: bool = False

class MetricComparison(BaseModel):
    metric_name: str
    unit: str
    baseline_value: float
    optimized_value: float
    change_value: float
    change_percent: float
    is_positive: bool

class OptimizationSchedule(BaseModel):
    hours: List[int]
    time_labels: List[str]
    baseline_grid_kw: List[float]
    optimized_grid_kw: List[float]
    baseline_cost_inr: List[float]
    optimized_cost_inr: List[float]
    solar_utilized_kw: List[float]
    solar_curtailed_kw: List[float]
    battery_charge_kw: List[float]
    battery_discharge_kw: List[float]
    battery_soc_percent: List[float]
    shifted_load_kw: List[float]
    solar_surplus_kw: List[float] = Field(default_factory=list)
    individual_flexible_schedules: Dict[str, List[float]] = Field(default_factory=dict)

class OptimizationResponse(BaseModel):
    success: bool
    deployment_level: DeploymentLevel
    status_summary: str
    schedule: OptimizationSchedule
    metrics_summary: List[MetricComparison]
    total_cost_baseline_inr: float
    total_cost_optimized_inr: float
    baseline_energy_cost_inr: float
    baseline_demand_charge_inr: float
    optimized_energy_cost_inr: float
    optimized_demand_charge_inr: float
    battery_degradation_cost_inr: float
    cost_savings_inr: float
    cost_savings_percent: float
    grid_reduction_kwh: float
    co2_avoided_tons: float
    peak_demand_baseline_kw: float
    peak_demand_optimized_kw: float
    peak_demand_shaved_kw: float
    recommendations: List[OptimizationRecommendation]
    computation_time_ms: float
    power_balance_max_error_kw: float = Field(default=0.0, description="Full precision solver power balance equality error (kW)")

class WhatIfRequest(BaseModel):
    solar_capacity_multiplier: float = Field(default=1.0, ge=0.0, le=3.0)
    battery_capacity_multiplier: float = Field(default=1.0, ge=0.0, le=3.0)
    tariff_rate_multiplier: float = Field(default=1.0, ge=0.5, le=2.5)
    cloud_cover_percent: float = Field(default=15.0, ge=0.0, le=100.0)
    flexible_load_shift_enabled: bool = True
    active_level: DeploymentLevel = "level_3_campus"

class WhatIfResponse(BaseModel):
    inputs: WhatIfRequest
    baseline_cost_inr: float
    simulated_cost_inr: float
    savings_inr: float
    savings_percent: float
    grid_consumption_kwh: float
    solar_generation_kwh: float
    solar_self_consumption_percent: float
    co2_emissions_tons: float
    co2_avoided_tons: float
    peak_grid_demand_kw: float
    peak_demand_shaved_kw: float
    explanation: str

class CSVUploadSummary(BaseModel):
    filename: str
    detected_format: str # "Interval 15-min Smart Meter" or "Monthly Utility Bill"
    total_records: int
    date_range: str
    interval_minutes: Optional[int] = None
    total_consumption_kwh: float
    peak_recorded_demand_kw: float
    has_solar_in_csv: bool
    total_solar_kwh: Optional[float] = 0.0
    estimated_bill_inr: float
    identified_wastage_kwh: float
    identified_savings_potential_inr: float
    inferred_level: DeploymentLevel
    data_quality_notes: List[str] = Field(default_factory=list)
    missing_records_count: int = 0
    duplicate_records_count: int = 0
    recommendation_summary: str
