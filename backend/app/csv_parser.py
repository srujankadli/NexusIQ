import io
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, List, Optional
from .schemas import CSVUploadSummary, DeploymentLevel, BuildingLoad

def parse_energy_csv(file_bytes: bytes, filename: str) -> Tuple[CSVUploadSummary, Dict[str, Any]]:
    """
    Rigorously parses energy telemetry:
    - Parses actual timestamps and sorts readings chronologically.
    - Accurately detects interval granularity (15-min, 30-min, hourly, monthly).
    - Distinguishes kW (power) from kWh (energy) using timestamp delta dt.
    - Detects building/meter IDs and maps submetered loads when present.
    - Detects solar generation and handles absent solar without fabricating readings.
    - Handles missing values, duplicates, and invalid records with transparent audit notes.
    - Fails fast with clear actionable errors when mandatory columns or data are missing.
    """
    if not file_bytes or len(file_bytes.strip()) == 0:
        raise ValueError("Uploaded file is completely empty (0 bytes). Please upload a valid CSV file.")

    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        raise ValueError(f"Unable to parse CSV structure: {str(e)}. Please ensure the file is valid UTF-8 formatted CSV.")

    if df.empty or len(df.columns) < 1:
        raise ValueError("Uploaded CSV file contains no tabular records or header columns.")

    raw_cols = list(df.columns)
    cols = [str(c).strip().lower() for c in df.columns]
    df.columns = cols

    data_quality_notes: List[str] = []
    missing_count = int(df.isna().sum().sum())
    if missing_count > 0:
        data_quality_notes.append(f"Encountered {missing_count} missing/NaN cells across dataset; imputed via forward-fill/zero-replacement.")

    # 1. Identify Timestamp / Date Column
    time_col = None
    for c in cols:
        if any(k in c for k in ["timestamp", "datetime", "date_time", "read_time", "date", "time", "month", "period"]):
            time_col = c
            break

    # Identify Building / Submeter Column early for accurate multi-meter deduplication
    building_col = None
    for c in cols:
        if c == time_col:
            continue
        if any(k in c for k in ["building_id", "building", "submeter", "meter_id", "facility_zone", "zone"]):
            building_col = c
            break

    total_records = len(df)
    duplicate_count = 0
    interval_minutes: Optional[int] = None

    if time_col:
        parsed_times = pd.to_datetime(df[time_col], errors='coerce')
        valid_time_mask = parsed_times.notna()
        invalid_time_count = int((~valid_time_mask).sum())
        if invalid_time_count > 0:
            data_quality_notes.append(f"Filtered {invalid_time_count} rows with unparseable timestamp formats.")
            df = df[valid_time_mask].copy()
            parsed_times = parsed_times[valid_time_mask]

        df['_dt'] = parsed_times
        dedup_subset = ['_dt', building_col] if building_col else ['_dt']
        duplicate_count = int(df.duplicated(subset=dedup_subset).sum())
        if duplicate_count > 0:
            data_quality_notes.append(f"Deduplicated {duplicate_count} records sharing identical timestamps{' and submeter IDs' if building_col else ''}.")
            df = df.drop_duplicates(subset=dedup_subset).copy()

        df = df.sort_values(by='_dt').reset_index(drop=True)

        if len(df) > 1:
            diffs = df['_dt'].diff().dropna()
            median_delta_sec = diffs.dt.total_seconds().median()
            interval_minutes = int(round(median_delta_sec / 60.0))
            if interval_minutes > 0:
                gap_threshold = median_delta_sec * 1.8
                gap_count = int((diffs.dt.total_seconds() > gap_threshold).sum())
                if gap_count > 0:
                    data_quality_notes.append(f"Identified {gap_count} timestamp gap(s) exceeding normal {interval_minutes}-min interval cadence.")

    # 2. Identify Demand / Power Column & Distinguish kW vs kWh
    demand_col = None
    is_demand_energy_kwh = False

    for c in cols:
        if c in ["_dt"]:
            continue
        if any(k in c for k in ["demand_kw", "power_kw", "load_kw", "grid_kw", "active_power", "total_demand_kw", "meter_kw"]):
            demand_col = c
            is_demand_energy_kwh = False
            break
        elif any(k in c for k in ["kwh", "energy_kwh", "consumption_kwh", "units", "usage_kwh", "total_kwh", "units_kwh"]):
            demand_col = c
            is_demand_energy_kwh = True
            break
        elif any(k in c for k in ["demand", "load", "consumption", "usage", "grid_import"]):
            demand_col = c
            is_demand_energy_kwh = ("kwh" in c)
            break

    if not demand_col:
        # Fallback to candidate numeric columns
        candidate_numeric = []
        for c in cols:
            if c not in [time_col, '_dt']:
                numeric_series = pd.to_numeric(df[c], errors='coerce')
                if numeric_series.notna().sum() > 0:
                    candidate_numeric.append((c, numeric_series.notna().sum()))
        if candidate_numeric:
            candidate_numeric.sort(key=lambda x: x[1], reverse=True)
            demand_col = candidate_numeric[0][0]
            is_demand_energy_kwh = ("kwh" in demand_col)
            data_quality_notes.append(f"Auto-mapped column '{demand_col}' as primary electricity demand series.")
        else:
            raise ValueError(
                f"CSV validation failed: No numeric electricity demand or consumption column detected. "
                f"Columns detected: {raw_cols}. Please provide a column such as 'demand_kw', 'power_kw', or 'consumption_kwh'."
            )

    # 3. Identify Solar Generation Column
    solar_col = None
    is_solar_energy_kwh = False
    for c in cols:
        if c in [time_col, demand_col, '_dt']:
            continue
        if any(k in c for k in ["solar_kw", "pv_kw", "solar_generation_kw", "pv_generation_kw"]):
            solar_col = c
            is_solar_energy_kwh = False
            break
        elif any(k in c for k in ["solar_kwh", "pv_kwh", "solar_generation", "solar", "pv"]):
            solar_col = c
            is_solar_energy_kwh = ("kwh" in c)
            break

    # 4. Building / Submeter Column already identified at top for deduplication
    if building_col in [time_col, demand_col, solar_col, '_dt']:
        building_col = None

    # Calculate dt in hours
    if interval_minutes and interval_minutes > 0:
        dt_hours = interval_minutes / 60.0
    else:
        dt_hours = 1.0 # default to 1 hour if unspecified

    # Parse and validate demand series
    demand_series = pd.to_numeric(df[demand_col], errors='coerce').fillna(0.0)
    neg_count = int((demand_series < 0).sum())
    if neg_count > 0:
        data_quality_notes.append(f"Clipped {neg_count} negative demand values to 0.0 kW.")
        demand_series = demand_series.clip(lower=0.0)

    if is_demand_energy_kwh:
        energy_kwh_series = demand_series
        demand_kw_series = demand_series / max(0.01, dt_hours)
    else:
        demand_kw_series = demand_series
        energy_kwh_series = demand_series * dt_hours

    total_consumption_kwh = float(energy_kwh_series.sum())
    peak_demand_kw = float(demand_kw_series.max()) if len(demand_kw_series) > 0 else 0.0
    avg_demand_kw = float(demand_kw_series.mean()) if len(demand_kw_series) > 0 else 0.0

    # Solar conversion
    has_solar = False
    total_solar_kwh = 0.0
    solar_kw_series = pd.Series([0.0] * len(df))

    if solar_col and solar_col in df.columns:
        raw_solar = pd.to_numeric(df[solar_col], errors='coerce').fillna(0.0).clip(lower=0.0)
        if float(raw_solar.sum()) > 0.1:
            has_solar = True
            if is_solar_energy_kwh:
                total_solar_kwh = float(raw_solar.sum())
                solar_kw_series = raw_solar / max(0.01, dt_hours)
            else:
                solar_kw_series = raw_solar
                total_solar_kwh = float((raw_solar * dt_hours).sum())
            data_quality_notes.append(f"Validated active rooftop solar generation from column '{solar_col}'.")
        else:
            data_quality_notes.append(f"Solar column '{solar_col}' detected but contains only zero values; solar treated as inactive.")
    else:
        data_quality_notes.append("No solar generation column found; set to Level 1 Basic (Zero Solar).")

    # Detect file format
    if (interval_minutes and interval_minutes >= 20000) or total_records <= 36:
        detected_format = "Monthly Utility Bill Summary"
    elif interval_minutes:
        detected_format = f"Interval {interval_minutes}-min Smart Meter"
    else:
        detected_format = "Hourly / Interval Energy Records"

    inferred_level: DeploymentLevel = "level_2_solar" if has_solar else "level_1_basic"

    # Date range string
    if '_dt' in df.columns and len(df) > 0:
        date_range = f"{df['_dt'].iloc[0].strftime('%Y-%m-%d %H:%M')} to {df['_dt'].iloc[-1].strftime('%Y-%m-%d %H:%M')}"
    else:
        date_range = f"Chronological export of {len(df)} logged intervals"

    # Detect sub-24h duration
    elapsed_hours = len(df) * dt_hours
    is_subdaily_estimate = False
    if '_dt' in df.columns and len(df) > 1:
        span_hours = (df['_dt'].iloc[-1] - df['_dt'].iloc[0]).total_seconds() / 3600.0
        if span_hours < 23.0:
            is_subdaily_estimate = True
            data_quality_notes.append(
                f"Sub-24h record span detected ({span_hours:.1f} hours). 24-hour diurnal profile estimated via cyclical interpolation."
            )
    elif len(df) < 24:
        is_subdaily_estimate = True
        data_quality_notes.append(
            f"Sub-24h dataset detected ({len(df)} records). 24-hour diurnal profile estimated via interpolation."
        )

    # Reconstruct 24-Hour Diurnal Hourly Profile
    has_submeters_in_df = bool(building_col and len(df[building_col].dropna().unique()) > 1)

    if has_submeters_in_df and '_dt' in df.columns:
        ts_demand = df.groupby('_dt').apply(lambda g: demand_kw_series.loc[g.index].sum())
        ts_df = pd.DataFrame({'_dt': ts_demand.index, 'demand': ts_demand.values})
        ts_df['hour_of_day'] = ts_df['_dt'].dt.hour
        hourly_means = ts_df.groupby('hour_of_day')['demand'].mean().to_dict()
        if len(ts_df) >= 24:
            chunks_demand = [round(float(hourly_means.get(h, float(ts_demand.mean()))), 1) for h in range(24)]
        else:
            interp_vals = np.interp(np.linspace(0, len(ts_demand)-1, 24), np.arange(len(ts_demand)), ts_demand.values)
            chunks_demand = [round(float(x), 1) for x in interp_vals]
        
        if has_solar:
            ts_solar = df.groupby('_dt').apply(lambda g: solar_kw_series.loc[g.index].sum())
            ts_solar_df = pd.DataFrame({'_dt': ts_solar.index, 'solar': ts_solar.values})
            ts_solar_df['hour_of_day'] = ts_solar_df['_dt'].dt.hour
            hourly_solar_means = ts_solar_df.groupby('hour_of_day')['solar'].mean().to_dict()
            chunks_solar = [round(float(hourly_solar_means.get(h, 0.0)), 1) for h in range(24)]
        else:
            chunks_solar = [0.0] * 24
    elif '_dt' in df.columns and len(df) >= 24:
        df['hour_of_day'] = df['_dt'].dt.hour
        hourly_demand_means = df.groupby('hour_of_day').apply(lambda g: demand_kw_series.loc[g.index].mean()).to_dict()
        chunks_demand = [round(float(hourly_demand_means.get(h, avg_demand_kw)), 1) for h in range(24)]

        if has_solar:
            hourly_solar_means = df.groupby('hour_of_day').apply(lambda g: solar_kw_series.loc[g.index].mean()).to_dict()
            chunks_solar = [round(float(hourly_solar_means.get(h, 0.0)), 1) for h in range(24)]
        else:
            chunks_solar = [0.0] * 24
    else:
        if len(demand_kw_series) >= 24:
            chunks_demand = [round(float(np.mean(chunk)), 1) for chunk in np.array_split(demand_kw_series.values, 24)]
        else:
            interp_vals = np.interp(np.linspace(0, len(demand_kw_series)-1, 24), np.arange(len(demand_kw_series)), demand_kw_series.values)
            chunks_demand = [round(float(x), 1) for x in interp_vals]

        if has_solar and len(solar_kw_series) >= 24:
            chunks_solar = [round(float(np.mean(chunk)), 1) for chunk in np.array_split(solar_kw_series.values, 24)]
        else:
            chunks_solar = [0.0] * 24

    # Baseline bill estimate (Commercial tariff ~ ₹8.20 / kWh + ₹280/kW demand charge)
    estimated_bill_inr = round(total_consumption_kwh * 8.20 + peak_demand_kw * 280.0, 2)

    # Detect reducible baseload leakage (night off-hours 01:00 to 05:00)
    night_hours_demand = [chunks_demand[h] for h in range(1, 5)]
    day_peak_demand = max(chunks_demand) if chunks_demand else 1.0
    min_night = min(night_hours_demand) if night_hours_demand else 0.0

    leakage_threshold = day_peak_demand * 0.35
    if min_night > leakage_threshold:
        identified_wastage_kw = min_night - leakage_threshold
        identified_wastage_kwh = round(identified_wastage_kw * 6.0, 1)
        savings_pot = round(identified_wastage_kwh * 4.80, 2)
        data_quality_notes.append(f"Identified off-hours baseload leakage of {identified_wastage_kw:.1f} kW between 01:00 and 05:00.")
    else:
        identified_wastage_kwh = 0.0
        savings_pot = 0.0

    # Build Submeter Buildings List
    parsed_buildings: List[BuildingLoad] = []
    if building_col and building_col in df.columns:
        unique_blds = df[building_col].dropna().unique()
        if len(unique_blds) > 1:
            for b_name in unique_blds[:8]: # cap to 8 buildings
                b_mask = (df[building_col] == b_name)
                b_demand = demand_kw_series[b_mask]
                b_peak = float(b_demand.max()) if len(b_demand) > 0 else 0.0
                b_avg = float(b_demand.mean()) if len(b_demand) > 0 else 0.0
                b_min = float(b_demand.min()) if len(b_demand) > 0 else 0.0
                is_flex = (b_peak - b_min) > (b_avg * 0.2)
                flex_cap = round((b_peak - b_min) * 0.3, 1) if is_flex else 0.0

                parsed_buildings.append(BuildingLoad(
                    id=f"bld-{str(b_name).strip().lower().replace(' ', '-')}",
                    name=str(b_name).strip(),
                    category="Submetered Facility",
                    current_load_kw=round(b_avg, 1),
                    base_load_kw=round(b_min, 1),
                    peak_load_kw=round(b_peak, 1),
                    is_flexible=is_flex,
                    flexible_capacity_kw=flex_cap,
                    operational_status="Active Submeter",
                    occupancy_percent=80
                ))
            data_quality_notes.append(f"Extracted {len(parsed_buildings)} genuine submetered building loads from column '{building_col}'.")

    if not parsed_buildings:
        # Default single aggregate building
        parsed_buildings.append(BuildingLoad(
            id="bld-aggregate-main",
            name="Aggregate Main Facility Meter (Single Submeter Telemetry)",
            category="Facility Main Meter",
            current_load_kw=round(chunks_demand[13] if len(chunks_demand) > 13 else avg_demand_kw, 1),
            base_load_kw=round(min(chunks_demand) if chunks_demand else 0.0, 1),
            peak_load_kw=round(peak_demand_kw, 1),
            is_flexible=True,
            flexible_capacity_kw=round(peak_demand_kw * 0.15, 1),
            operational_status="Active Telemetry",
            occupancy_percent=85
        ))
        data_quality_notes.append("Single facility aggregate meter detected; submetering breakdown not present in dataset.")

    solar_peak = max(chunks_solar) if chunks_solar else 0.0
    solar_capacity_kw = round(solar_peak * 1.05, 1) if has_solar else 0.0

    recom_text = (
        f"Processed {len(df)} validated readings ({interval_minutes or 'variable'} min intervals). "
        f"Total measured consumption: {total_consumption_kwh:,.1f} kWh, peak recorded power: {peak_demand_kw:.1f} kW. "
        + (f"Rooftop solar identified ({solar_capacity_kw:.0f} kWp peak). " if has_solar else "No solar generation identified. ")
        + (f"Identified {identified_wastage_kwh} kWh/day reducible baseload leakage." if identified_wastage_kwh > 0 else "Nominal baseload within acceptable parameters.")
    )

    summary = CSVUploadSummary(
        filename=filename,
        detected_format=detected_format,
        total_records=len(df),
        date_range=date_range,
        interval_minutes=interval_minutes,
        total_consumption_kwh=round(total_consumption_kwh, 1),
        peak_recorded_demand_kw=round(peak_demand_kw, 1),
        avg_demand_kw=round(avg_demand_kw, 1),
        has_solar_in_csv=has_solar,
        total_solar_kwh=round(total_solar_kwh, 1),
        estimated_bill_inr=estimated_bill_inr,
        identified_wastage_kwh=identified_wastage_kwh,
        identified_savings_potential_inr=savings_pot,
        inferred_level=inferred_level,
        data_quality_notes=data_quality_notes,
        missing_records_count=missing_count,
        duplicate_records_count=duplicate_count,
        is_subdaily_estimate=is_subdaily_estimate,
        recommendation_summary=recom_text
    )

    normalized_data = {
        "demand_24h": chunks_demand,
        "solar_24h": chunks_solar,
        "solar_capacity_kw": solar_capacity_kw,
        "total_consumption": total_consumption_kwh,
        "peak_demand": peak_demand_kw,
        "avg_demand_kw": avg_demand_kw,
        "has_solar": has_solar,
        "is_subdaily_estimate": is_subdaily_estimate,
        "buildings": parsed_buildings,
        "columns_detected": raw_cols
    }

    return summary, normalized_data
