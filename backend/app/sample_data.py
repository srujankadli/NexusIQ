import numpy as np
from typing import List, Dict, Any
from .schemas import BuildingLoad, FacilityConfig

def get_time_labels() -> List[str]:
    labels = []
    for h in range(24):
        if h == 0:
            labels.append("12 AM")
        elif h < 12:
            labels.append(f"{h} AM")
        elif h == 12:
            labels.append("12 PM")
        else:
            labels.append(f"{h - 12} PM")
    return labels

def get_tou_tariff(hour: int, config: FacilityConfig) -> float:
    # Karnataka/Bangalore (BESCOM) standard commercial ToU tariff structure:
    # Peak: 18:00 - 22:00 (₹11.50/kWh)
    # Normal: 06:00 - 18:00 and 22:00 - 23:00 (₹7.50/kWh)
    # Off-Peak: 23:00 - 06:00 (₹4.80/kWh)
    if config.tariff_type == "flat_rate":
        return config.grid_tariff_normal_inr
    if 18 <= hour < 22:
        return config.grid_tariff_peak_inr
    elif 23 <= hour or hour < 6:
        return config.grid_tariff_offpeak_inr
    else:
        return config.grid_tariff_normal_inr

def get_solar_irradiance_curve(cloud_cover: float = 15.0) -> np.ndarray:
    """Returns 24h Global Horizontal Irradiance (GHI) in W/m²."""
    hours = np.arange(24)
    # Solar window roughly 6:00 AM to 6:30 PM, peak at 12:30 PM (~950 W/m² clear sky)
    irradiance = np.zeros(24)
    for h in range(6, 19):
        # bell curve peaked at 12.5
        val = np.sin((h - 6) / 12.0 * np.pi) ** 1.6 * 960.0
        # attenuate by cloud cover
        cloud_factor = max(0.1, 1.0 - (cloud_cover / 100.0) * 0.75)
        irradiance[h] = max(0.0, val * cloud_factor)
    return irradiance

def get_temperature_curve() -> np.ndarray:
    """Returns 24h ambient temperature in °C."""
    # Min at 5 AM (20°C), Max at 2 PM (32°C) in Bengaluru climate
    hours = np.arange(24)
    return 20.0 + 12.0 * np.sin((hours - 5) / 18.0 * np.pi).clip(0, 1)

def get_base_campus_demand(level: str = "level_3_campus") -> np.ndarray:
    """
    Realistic 24h demand curve in kW.
    For Level 3 (Entire NHCE Campus): ~1,500 kW baseload, peaking at ~4,800 kW at 1:30 PM.
    For Level 1 (Single building / Basic): ~250 kW baseload, peaking at ~800 kW.
    """
    hours = np.arange(24)
    if level == "level_1_basic":
        # Single facility
        base = 220.0
        academic_peak = 520.0 * np.exp(-((hours - 13.0) ** 2) / 18.0)
        evening_hostel = 180.0 * np.exp(-((hours - 20.0) ** 2) / 8.0)
        demand = base + academic_peak + evening_hostel
    elif level == "level_2_solar":
        # Mid-sized institution with rooftop PV
        base = 900.0
        academic_peak = 2200.0 * np.exp(-((hours - 13.0) ** 2) / 20.0)
        evening_hostel = 700.0 * np.exp(-((hours - 20.0) ** 2) / 10.0)
        demand = base + academic_peak + evening_hostel
    else:
        # Full campus (Ideathon Dashboard: total ~4,820 kWh, peak ~4.8 MW total campus power)
        base = 1450.0
        academic_peak = 2950.0 * np.exp(-((hours - 13.5) ** 2) / 22.0)
        evening_peak = 1100.0 * np.exp(-((hours - 20.0) ** 2) / 9.0)
        demand = base + academic_peak + evening_peak
    return np.round(demand, 1)

def get_campus_buildings(level: str = "level_3_campus") -> List[BuildingLoad]:
    """Returns the sub-metered buildings in NHCE campus."""
    if level == "level_1_basic":
        return [
            BuildingLoad(
                id="bld-1",
                name="Main Academic & Admin Block",
                category="Academic",
                current_load_kw=480.0,
                base_load_kw=120.0,
                peak_load_kw=650.0,
                is_flexible=True,
                flexible_capacity_kw=80.0,
                operational_status="High Demand",
                temperature_c=25.2,
                occupancy_percent=88
            ),
            BuildingLoad(
                id="bld-2",
                name="Utility & Water Pump Room",
                category="Utilities & Pumps",
                current_load_kw=90.0,
                base_load_kw=30.0,
                peak_load_kw=150.0,
                is_flexible=True,
                flexible_capacity_kw=60.0,
                operational_status="Shift Eligible",
                temperature_c=28.0,
                occupancy_percent=10
            )
        ]
    
    return [
        BuildingLoad(
            id="bld-1",
            name="Academic Block A & B (Classrooms)",
            category="Academic",
            current_load_kw=1420.0,
            base_load_kw=320.0,
            peak_load_kw=1750.0,
            is_flexible=True,
            flexible_capacity_kw=250.0, # HVAC pre-cooling
            operational_status="High Demand",
            temperature_c=24.1,
            occupancy_percent=92
        ),
        BuildingLoad(
            id="bld-2",
            name="Research & High-Performance Computing Lab",
            category="Laboratories",
            current_load_kw=980.0,
            base_load_kw=450.0,
            peak_load_kw=1100.0,
            is_flexible=False, # Critical research servers
            flexible_capacity_kw=0.0,
            operational_status="Normal",
            temperature_c=20.5,
            occupancy_percent=75
        ),
        BuildingLoad(
            id="bld-3",
            name="Central Library & 1000-seat Auditorium",
            category="Auditorium & Library",
            current_load_kw=580.0,
            base_load_kw=110.0,
            peak_load_kw=850.0,
            is_flexible=True,
            flexible_capacity_kw=120.0,
            operational_status="Normal",
            temperature_c=23.4,
            occupancy_percent=60
        ),
        BuildingLoad(
            id="bld-4",
            name="Student Hostels & Central Dining Complex",
            category="Hostel & Dining",
            current_load_kw=1240.0,
            base_load_kw=380.0,
            peak_load_kw=1400.0,
            is_flexible=True,
            flexible_capacity_kw=160.0, # Water heaters
            operational_status="Normal",
            temperature_c=26.0,
            occupancy_percent=85
        ),
        BuildingLoad(
            id="bld-5",
            name="Campus Utility, STP & Raw Water Treatment",
            category="Utilities & Pumps",
            current_load_kw=580.0,
            base_load_kw=190.0,
            peak_load_kw=700.0,
            is_flexible=True,
            flexible_capacity_kw=280.0, # Water lifting & pump shifting
            operational_status="Optimized",
            temperature_c=29.2,
            occupancy_percent=15
        )
    ]

def generate_sample_csv_content() -> str:
    """Generates a downloadable sample 30-day interval meter CSV."""
    lines = ["timestamp,demand_kw,solar_generation_kw,grid_import_kw,tariff_inr_per_kwh,building_id"]
    days = 7
    for d in range(1, days + 1):
        for h in range(24):
            time_str = f"2026-10-{d:02d}T{h:02d}:00:00"
            demand = round(1200 + 1500 * np.sin((h - 6) / 14 * np.pi) ** 2 + np.random.normal(0, 40), 1)
            solar = 0.0
            if 6 <= h <= 18:
                solar = round(max(0.0, 1800 * np.sin((h - 6) / 12 * np.pi) ** 1.8 + np.random.normal(0, 30)), 1)
            grid = round(max(0.0, demand - solar), 1)
            tariff = 11.5 if (18 <= h < 22) else (4.8 if (h >= 23 or h < 6) else 7.5)
            lines.append(f"{time_str},{demand},{solar},{grid},{tariff},NHCE-MAIN")
    return "\n".join(lines)

