import datetime
from typing import Optional, List, Dict, Any
from .schemas import (
    FacilityConfig,
    DeploymentLevel,
    BuildingLoad,
    CSVUploadSummary
)
from .sample_data import get_campus_buildings, get_base_campus_demand, get_solar_irradiance_curve

class ActiveDataset:
    def __init__(
        self,
        source_type: str = "demo",
        filename: str = "nhce_smart_meter_sample.csv",
        display_name: str = "Demo Benchmark (NHCE Campus)",
        total_records: int = 24,
        date_range: str = "24-Hour Diurnal Campus Operational Baseline",
        interval_minutes: Optional[int] = 60,
        columns_detected: Optional[List[str]] = None,
        missing_values_count: int = 0,
        data_quality_notes: Optional[List[str]] = None,
        demand_24h: Optional[List[float]] = None,
        total_consumption_kwh: float = 78564.0,
        peak_demand_kw: float = 5973.4,
        avg_demand_kw: float = 3273.5,
        has_solar: bool = True,
        solar_installed_capacity_kw: float = 2100.0,
        solar_24h: Optional[List[float]] = None,
        total_solar_kwh: float = 11330.0,
        has_battery: bool = True,
        battery_capacity_kwh: float = 1200.0,
        battery_max_power_kw: float = 800.0,
        has_submeters: bool = False,
        buildings: Optional[List[BuildingLoad]] = None,
        inferred_level: DeploymentLevel = "level_3_campus",
        is_subdaily_estimate: bool = False
    ):
        self.source_type = source_type # "demo" | "uploaded"
        self.filename = filename
        self.display_name = display_name
        self.upload_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.total_records = total_records
        self.date_range = date_range
        self.interval_minutes = interval_minutes
        self.columns_detected = list(columns_detected) if columns_detected is not None else ["timestamp", "demand_kw", "solar_kw"]
        self.missing_values_count = missing_values_count
        self.data_quality_notes = list(data_quality_notes) if data_quality_notes is not None else []
        self.demand_24h = [float(x) for x in demand_24h] if demand_24h is not None else [float(x) for x in get_base_campus_demand("level_3_campus")]
        self.total_consumption_kwh = total_consumption_kwh
        self.peak_demand_kw = peak_demand_kw
        self.avg_demand_kw = avg_demand_kw
        self.is_subdaily_estimate = is_subdaily_estimate
        self.has_solar = has_solar
        self.solar_installed_capacity_kw = solar_installed_capacity_kw
        
        if solar_24h is not None:
            self.solar_24h = [float(x) for x in solar_24h]
        elif has_solar and solar_installed_capacity_kw > 0:
            irr = get_solar_irradiance_curve(15.0)
            self.solar_24h = [round(solar_installed_capacity_kw * (g / 1000.0) * 0.94, 1) if g > 10 else 0.0 for g in irr]
        else:
            self.solar_24h = [0.0] * 24

        self.total_solar_kwh = total_solar_kwh if total_solar_kwh > 0 else sum(self.solar_24h)
        self.has_battery = has_battery
        self.battery_capacity_kwh = battery_capacity_kwh
        self.battery_max_power_kw = battery_max_power_kw
        self.has_submeters = has_submeters
        self.buildings = buildings or []
        self.inferred_level = inferred_level

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type,
            "filename": self.filename,
            "display_name": self.display_name,
            "upload_timestamp": self.upload_timestamp,
            "total_records": self.total_records,
            "date_range": self.date_range,
            "interval_minutes": self.interval_minutes,
            "columns_detected": self.columns_detected,
            "missing_values_count": self.missing_values_count,
            "data_quality_notes": self.data_quality_notes,
            "total_consumption_kwh": round(self.total_consumption_kwh, 1),
            "peak_demand_kw": round(self.peak_demand_kw, 1),
            "avg_demand_kw": round(self.avg_demand_kw, 1),
            "has_solar": self.has_solar,
            "solar_installed_capacity_kw": round(self.solar_installed_capacity_kw, 1),
            "total_solar_kwh": round(self.total_solar_kwh, 1),
            "has_battery": self.has_battery,
            "battery_capacity_kwh": round(self.battery_capacity_kwh, 1),
            "battery_max_power_kw": round(self.battery_max_power_kw, 1),
            "has_submeters": self.has_submeters,
            "inferred_level": self.inferred_level,
            "is_subdaily_estimate": self.is_subdaily_estimate
        }

class DatasetManager:
    """
    Centralized Single Source of Truth for NexusIQ.
    Manages whether the system is operating in Demo Mode or Uploaded Data Mode.
    Ensures all modules consume the exact same active dataset.
    """
    _instance = None

    def __init__(self):
        self.active: ActiveDataset = self._create_demo_dataset("level_3_campus")

    @classmethod
    def get_instance(cls) -> "DatasetManager":
        if cls._instance is None:
            cls._instance = DatasetManager()
        return cls._instance

    def _create_demo_dataset(self, level: DeploymentLevel = "level_3_campus") -> ActiveDataset:
        demand = get_base_campus_demand(level)
        total_kwh = sum(demand)
        peak_kw = max(demand)
        avg_kw = total_kwh / len(demand)

        has_solar = level != "level_1_basic"
        solar_cap = 2100.0 if level == "level_3_campus" else (1200.0 if level == "level_2_solar" else 0.0)
        has_bat = level == "level_3_campus"
        bat_cap = 1200.0 if has_bat else 0.0
        bat_power = 800.0 if has_bat else 0.0

        level_name = "Level 3: Microgrid" if level == "level_3_campus" else ("Level 2: Solar PV" if level == "level_2_solar" else "Level 1: Basic (Bill/CSV)")

        return ActiveDataset(
            source_type="demo",
            filename="nhce_smart_meter_sample.csv",
            display_name=f"Demo Benchmark ({level_name})",
            total_records=24,
            date_range="Diurnal 24h Baseline Profile",
            interval_minutes=60,
            columns_detected=["timestamp", "demand_kw", "solar_kw"],
            missing_values_count=0,
            data_quality_notes=["Loaded synthetic NHCE campus benchmark dataset."],
            demand_24h=demand,
            total_consumption_kwh=total_kwh,
            peak_demand_kw=peak_kw,
            avg_demand_kw=avg_kw,
            has_solar=has_solar,
            solar_installed_capacity_kw=solar_cap,
            has_battery=has_bat,
            battery_capacity_kwh=bat_cap,
            battery_max_power_kw=bat_power,
            has_submeters=False,
            buildings=get_campus_buildings(level),
            inferred_level=level
        )

    def set_uploaded_dataset(self, summary: CSVUploadSummary, parsed_data: Dict[str, Any]) -> ActiveDataset:
        """
        Transitions the platform into Uploaded Data Mode.
        All modules will now derive calculations strictly from this dataset.
        """
        demand_24h = parsed_data["demand_24h"]
        solar_24h = parsed_data.get("solar_24h", [0.0] * 24)
        has_solar = parsed_data.get("has_solar", False)
        solar_cap = parsed_data.get("solar_capacity_kw", (max(solar_24h) if has_solar else 0.0))

        buildings = parsed_data.get("buildings", [])
        has_submeters = len(buildings) > 1

        self.active = ActiveDataset(
            source_type="uploaded",
            filename=summary.filename,
            display_name=f"Uploaded: {summary.filename}",
            total_records=summary.total_records,
            date_range=summary.date_range,
            interval_minutes=summary.interval_minutes,
            columns_detected=parsed_data.get("columns_detected", []),
            missing_values_count=summary.missing_records_count,
            data_quality_notes=summary.data_quality_notes,
            demand_24h=demand_24h,
            total_consumption_kwh=summary.total_consumption_kwh,
            peak_demand_kw=summary.peak_recorded_demand_kw,
            avg_demand_kw=summary.avg_demand_kw if (summary.avg_demand_kw and summary.avg_demand_kw > 0) else float(parsed_data.get("avg_demand_kw", summary.total_consumption_kwh / max(1.0, float(len(demand_24h))))),
            has_solar=has_solar,
            solar_installed_capacity_kw=solar_cap,
            solar_24h=solar_24h,
            total_solar_kwh=summary.total_solar_kwh,
            has_battery=False, # Never invent battery capacity unless specified
            battery_capacity_kwh=0.0,
            battery_max_power_kw=0.0,
            has_submeters=has_submeters,
            buildings=buildings,
            inferred_level=summary.inferred_level,
            is_subdaily_estimate=summary.is_subdaily_estimate
        )
        return self.active

    def switch_to_demo(self, level: DeploymentLevel = "level_3_campus") -> ActiveDataset:
        """
        Restores the platform to standard synthetic Demo Benchmark mode.
        """
        self.active = self._create_demo_dataset(level)
        return self.active

    def get_facility_config(self) -> FacilityConfig:
        """
        Constructs a FacilityConfig guaranteed to align with the active dataset.
        """
        act = self.active
        name = f"NHCE Campus [{act.filename}]" if act.source_type == "uploaded" else "NHCE Green Campus"
        contracted_demand = max(act.peak_demand_kw * 1.1, 1000.0)

        return FacilityConfig(
            name=name,
            level=act.inferred_level,
            grid_contracted_demand_kw=round(contracted_demand, 1),
            has_solar=act.has_solar,
            solar_installed_capacity_kw=round(act.solar_installed_capacity_kw, 1),
            has_battery=act.has_battery,
            battery_capacity_kwh=round(act.battery_capacity_kwh, 1),
            battery_max_power_kw=round(act.battery_max_power_kw, 1),
            has_flexible_loads=True
        )

# Global dataset manager instance
dataset_manager = DatasetManager.get_instance()
