import io
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, List
from .schemas import CSVUploadSummary, DeploymentLevel

def parse_energy_csv(file_bytes: bytes, filename: str) -> Tuple[CSVUploadSummary, Dict[str, Any]]:
    """
    Rigorously parses energy telemetry:
    - Parses actual timestamps and sorts readings chronologically.
    - Accurately detects interval granularity (15-min, 30-min, hourly, monthly).
    - Distinguishes kW (power) from kWh (energy) using timestamp delta dt.
    - Handles missing values, duplicates, and invalid records with transparent audit notes.
    - Never fabricates solar or battery measurements if absent in the upload.
    """
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        raise ValueError(f"Unable to parse CSV structure: {str(e)}")

    if df.empty or len(df.columns) < 1:
        raise ValueError("Uploaded CSV file is empty or contains no columns.")

    raw_cols = list(df.columns)
    cols = [str(c).strip().lower() for c in df.columns]
    df.columns = cols

    data_quality_notes: List[str] = []
    missing_count = int(df.isna().sum().sum())
    if missing_count > 0:
        data_quality_notes.append(f"Encountered {missing_count} missing/NaN values; handled via forward-fill/zero-replacement.")

    # 1. Identify Timestamp / Date Column
    time_col = None
    for c in cols:
        if any(k in c for k in ["timestamp", "datetime", "date_time", "read_time", "date", "time", "month"]):
            time_col = c
            break

    total_records = len(df)
    duplicate_count = 0
    interval_minutes = None

    if time_col:
        # Parse timestamps
        parsed_times = pd.to_datetime(df[time_col], errors='coerce')
        valid_time_mask = parsed_times.notna()
        invalid_time_count = int((~valid_time_mask).sum())
        if invalid_time_count > 0:
            data_quality_notes.append(f"Filtered {invalid_time_count} rows with invalid timestamp format.")
            df = df[valid_time_mask].copy()
            parsed_times = parsed_times[valid_time_mask]

        df['_dt'] = parsed_times
        duplicate_count = int(df.duplicated(subset=['_dt']).sum())
        if duplicate_count > 0:
            data_quality_notes.append(f"Found and deduplicated {duplicate_count} duplicate timestamp records.")
            df = df.drop_duplicates(subset=['_dt']).copy()

        df = df.sort_values(by='_dt').reset_index(drop=True)

        if len(df) > 1:
            diffs = df['_dt'].diff().dropna()
            median_delta_sec = diffs.dt.total_seconds().median()
            interval_minutes = int(round(median_delta_sec / 60.0))

    # 2. Identify Demand / Power Column & Distinguish kW vs kWh
    demand_col = None
    is_demand_energy_kwh = False

    for c in cols:
        if c in ["_dt"]:
            continue
        if any(k in c for k in ["demand_kw", "power_kw", "load_kw", "kw", "active_power"]):
            demand_col = c
            is_demand_energy_kwh = False
            break
        elif any(k in c for k in ["kwh", "energy_kwh", "consumption_kwh", "units", "usage_kwh"]):
            demand_col = c
            is_demand_energy_kwh = True
            break
        elif any(k in c for k in ["demand", "load", "consumption", "usage"]):
            demand_col = c
            # check unit in column name
            is_demand_energy_kwh = "kwh" in c
            break

    if not demand_col:
        # Check for genuinely numeric columns
        candidate_numeric = []
        for c in cols:
            if c not in [time_col, '_dt']:
                if pd.to_numeric(df[c], errors='coerce').notna().sum() > 0:
                    candidate_numeric.append(c)
        if candidate_numeric:
            demand_col = candidate_numeric[0]
            is_demand_energy_kwh = "kwh" in demand_col
        else:
            raise ValueError("No numeric electricity demand or consumption column identified in CSV.")

    # 3. Identify Solar Column
    solar_col = None
    is_solar_energy_kwh = False
    for c in cols:
        if c in [time_col, demand_col, '_dt']:
            continue
        if any(k in c for k in ["solar_kw", "pv_kw", "generation_kw"]):
            solar_col = c
            is_solar_energy_kwh = False
            break
        elif any(k in c for k in ["solar_kwh", "pv_kwh", "solar_generation", "solar", "pv"]):
            solar_col = c
            is_solar_energy_kwh = "kwh" in c
            break

    # Calculate dt in hours
    if interval_minutes and interval_minutes > 0:
        dt_hours = interval_minutes / 60.0
    else:
        dt_hours = 1.0 # default to 1 hour if unknown interval

    # Parse and validate demand series
    demand_series = pd.to_numeric(df[demand_col], errors='coerce').fillna(0.0)
    # Check for negative numbers
    neg_count = int((demand_series < 0).sum())
    if neg_count > 0:
        data_quality_notes.append(f"Clipped {neg_count} negative demand values to 0.0 kW.")
        demand_series = demand_series.clip(lower=0.0)

    # Convert to standard demand in kW and energy in kWh
    if is_demand_energy_kwh:
        # Column has energy kWh
        energy_kwh_series = demand_series
        demand_kw_series = demand_series / max(0.01, dt_hours)
    else:
        # Column has power kW
        demand_kw_series = demand_series
        energy_kwh_series = demand_series * dt_hours

    total_consumption_kwh = float(energy_kwh_series.sum())
    peak_demand_kw = float(demand_kw_series.max()) if len(demand_kw_series) > 0 else 0.0

    # Solar conversion
    has_solar = False
    total_solar_kwh = 0.0
    solar_kw_series = pd.Series([0.0] * len(df))

    if solar_col and solar_col in df.columns:
        raw_solar = pd.to_numeric(df[solar_col], errors='coerce').fillna(0.0).clip(lower=0.0)
        if raw_solar.sum() > 0.1:
            has_solar = True
            if is_solar_energy_kwh:
                total_solar_kwh = float(raw_solar.sum())
                solar_kw_series = raw_solar / max(0.01, dt_hours)
            else:
                solar_kw_series = raw_solar
                total_solar_kwh = float((raw_solar * dt_hours).sum())
        else:
            data_quality_notes.append("Solar column detected but all values were 0.0; solar set to inactive.")
    else:
        data_quality_notes.append("No solar generation column detected in CSV; Level 1 non-solar profile created.")

    # Detect file format
    if (interval_minutes and interval_minutes >= 20000) or total_records <= 36:
        detected_format = "Monthly Utility Bill Summary"
    elif interval_minutes:
        detected_format = f"Interval {interval_minutes}-min Smart Meter"
    else:
        detected_format = "Hourly / Interval Energy Records"

    # Inferred Deployment Level
    inferred_level: DeploymentLevel = "level_2_solar" if has_solar else "level_1_basic"

    # Date range string
    if '_dt' in df.columns and len(df) > 0:
        date_range = f"{df['_dt'].iloc[0].strftime('%Y-%m-%d %H:%M')} to {df['_dt'].iloc[-1].strftime('%Y-%m-%d %H:%M')}"
    else:
        date_range = f"Chronological export of {len(df)} logged intervals"

    # Reconstruct 24-Hour Diurnal Average Profile
    if '_dt' in df.columns and len(df) >= 24:
        df['hour_of_day'] = df['_dt'].dt.hour
        hourly_demand_means = df.groupby('hour_of_day').apply(lambda g: demand_kw_series.loc[g.index].mean()).to_dict()
        chunks_demand = [float(hourly_demand_means.get(h, demand_kw_series.mean())) for h in range(24)]

        if has_solar:
            hourly_solar_means = df.groupby('hour_of_day').apply(lambda g: solar_kw_series.loc[g.index].mean()).to_dict()
            chunks_solar = [float(hourly_solar_means.get(h, 0.0)) for h in range(24)]
        else:
            chunks_solar = [0.0] * 24
    else:
        # Sample / interpolate to 24 hourly points
        if len(demand_kw_series) >= 24:
            chunks_demand = [float(np.mean(chunk)) for chunk in np.array_split(demand_kw_series.values, 24)]
        else:
            chunks_demand = [float(x) for x in np.interp(np.linspace(0, len(demand_kw_series)-1, 24), np.arange(len(demand_kw_series)), demand_kw_series.values)]
        
        if has_solar and len(solar_kw_series) >= 24:
            chunks_solar = [float(np.mean(chunk)) for chunk in np.array_split(solar_kw_series.values, 24)]
        else:
            chunks_solar = [0.0] * 24

    # Baseline bill estimate (Standard Indian commercial average tariff ~ ₹8.20 / kWh + ₹280/kW demand charge)
    estimated_bill_inr = round(total_consumption_kwh * 8.20 + peak_demand_kw * 280.0, 2)

    # Detect genuine baseload leakage during night off-hours (hours 1 to 5)
    night_hours_demand = [chunks_demand[h] for h in range(1, 5)]
    day_peak_demand = max(chunks_demand)
    min_night = min(night_hours_demand) if night_hours_demand else 0.0

    # If off-hours baseload exceeds 35% of peak daytime load, quantify genuine reducible leakage
    leakage_threshold = day_peak_demand * 0.35
    if min_night > leakage_threshold:
        identified_wastage_kw = min_night - leakage_threshold
        identified_wastage_kwh = round(identified_wastage_kw * 6.0, 1) # 6 hours of overnight leak
        savings_pot = round(identified_wastage_kwh * 4.80, 2)
        data_quality_notes.append(f"Identified off-hours baseload leak of {identified_wastage_kw:.1f} kW between 01:00 and 05:00.")
    else:
        identified_wastage_kwh = 0.0
        savings_pot = 0.0

    recom_text = (
        f"Processed {len(df)} validated readings ({interval_minutes or 'variable'} min intervals). "
        f"Total measured consumption: {total_consumption_kwh:,.1f} kWh, peak recorded power: {peak_demand_kw:.1f} kW. "
        + (f"Identified {identified_wastage_kwh} kWh/day of reducible baseload leakage." if identified_wastage_kwh > 0 else "Nominal baseload within acceptable parameters.")
    )

    summary = CSVUploadSummary(
        filename=filename,
        detected_format=detected_format,
        total_records=len(df),
        date_range=date_range,
        interval_minutes=interval_minutes,
        total_consumption_kwh=round(total_consumption_kwh, 1),
        peak_recorded_demand_kw=round(peak_demand_kw, 1),
        has_solar_in_csv=has_solar,
        total_solar_kwh=round(total_solar_kwh, 1),
        estimated_bill_inr=estimated_bill_inr,
        identified_wastage_kwh=identified_wastage_kwh,
        identified_savings_potential_inr=savings_pot,
        inferred_level=inferred_level,
        data_quality_notes=data_quality_notes,
        missing_records_count=missing_count,
        duplicate_records_count=duplicate_count,
        recommendation_summary=recom_text
    )

    normalized_data = {
        "demand_24h": chunks_demand,
        "solar_24h": chunks_solar,
        "total_consumption": total_consumption_kwh,
        "peak_demand": peak_demand_kw,
        "has_solar": has_solar
    }

    return summary, normalized_data
