import React, { useState, useEffect } from 'react';
import {
  Sliders,
  Sun,
  BatteryCharging,
  DollarSign,
  CloudRain,
  RotateCcw,
  Sparkles,
  Info,
  CheckCircle2,
  TrendingDown,
  Save
} from 'lucide-react';
import { WhatIfRequest, WhatIfResponse, FacilityConfig } from '../types';
import { api } from '../services/api';

interface WhatIfSimulatorViewProps {
  facilityConfig: FacilityConfig | null;
  onApplyConfig?: (updated: FacilityConfig) => Promise<void>;
}

export const WhatIfSimulatorView: React.FC<WhatIfSimulatorViewProps> = ({
  facilityConfig,
  onApplyConfig,
}) => {
  const [solarMult, setSolarMult] = useState(1.0);
  const [batteryMult, setBatteryMult] = useState(1.0);
  const [tariffMult, setTariffMult] = useState(1.0);
  const [cloudCover, setCloudCover] = useState(15.0);
  const [flexEnabled, setFlexEnabled] = useState(true);

  const [simResult, setSimResult] = useState<WhatIfResponse | null>(null);
  const [applying, setApplying] = useState(false);
  const [applyFeedback, setApplyFeedback] = useState<string | null>(null);

  const baseSolar = (facilityConfig?.solar_installed_capacity_kw && facilityConfig.solar_installed_capacity_kw > 0)
    ? facilityConfig.solar_installed_capacity_kw
    : 2100;
  const baseBattery = (facilityConfig?.battery_capacity_kwh && facilityConfig.battery_capacity_kwh > 0)
    ? facilityConfig.battery_capacity_kwh
    : 1200;

  async function runSim() {
    try {
      const req: WhatIfRequest = {
        solar_capacity_multiplier: solarMult,
        battery_capacity_multiplier: batteryMult,
        tariff_rate_multiplier: tariffMult,
        cloud_cover_percent: cloudCover,
        flexible_load_shift_enabled: flexEnabled,
        active_level: facilityConfig?.level || 'level_3_campus',
      };
      const res = await api.runWhatIf(req);
      setSimResult(res);
    } catch (err) {
      console.error(err);
    }
  }

  useEffect(() => {
    runSim();
  }, [solarMult, batteryMult, tariffMult, cloudCover, flexEnabled, facilityConfig?.level]);

  function resetDefaults() {
    setSolarMult(1.0);
    setBatteryMult(1.0);
    setTariffMult(1.0);
    setCloudCover(15.0);
    setFlexEnabled(true);
  }

  async function handleApplyToPlatform() {
    if (!facilityConfig || !onApplyConfig) return;
    setApplying(true);
    try {
      const newSolarCap = Math.round(baseSolar * solarMult);
      const newBatCap = Math.round(baseBattery * batteryMult);
      const updated: FacilityConfig = {
        ...facilityConfig,
        solar_installed_capacity_kw: newSolarCap,
        has_solar: newSolarCap > 0,
        battery_capacity_kwh: newBatCap,
        has_battery: newBatCap > 0,
        grid_tariff_peak_inr: Number((facilityConfig.grid_tariff_peak_inr * tariffMult).toFixed(2)),
        grid_tariff_normal_inr: Number((facilityConfig.grid_tariff_normal_inr * tariffMult).toFixed(2)),
        grid_tariff_offpeak_inr: Number((facilityConfig.grid_tariff_offpeak_inr * tariffMult).toFixed(2)),
      };
      await onApplyConfig(updated);
      setApplyFeedback('Simulated capacity & tariff configuration successfully applied to platform!');
      setTimeout(() => setApplyFeedback(null), 5000);
    } catch (err) {
      console.error(err);
    } finally {
      setApplying(false);
    }
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-400 border border-purple-500/30 flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5" />
              Scenario Simulation & Capacity Planning
            </span>
            <span className="text-xs text-slate-400">Consistent & Transparent Formulas</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white">
            Interactive What-If Energy & Tariff Simulator
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Simulate expanding solar arrays, sizing battery storage, surviving tariff surges, or extreme monsoon weather.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={resetDefaults}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg transition cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Defaults</span>
          </button>
          {onApplyConfig && (
            <button
              onClick={handleApplyToPlatform}
              disabled={applying}
              className="flex items-center gap-1.5 px-3.5 py-1.5 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-purple-600/20 transition cursor-pointer"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{applying ? 'Applying...' : 'Apply to Platform'}</span>
            </button>
          )}
        </div>
      </div>

      {applyFeedback && (
        <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-purple-400 shrink-0" />
          <span>{applyFeedback}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sliders Control Panel */}
        <div className="bg-slate-900/90 border border-slate-800 p-6 rounded-2xl shadow-xl space-y-5">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Sliders className="w-4 h-4 text-emerald-400" />
            Simulation Parameters
          </h2>

          {/* Slider 1: Solar */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-slate-300 flex items-center gap-1.5">
                <Sun className="w-3.5 h-3.5 text-amber-400" /> Solar PV Capacity
              </span>
              <span className="font-bold text-amber-400">{solarMult.toFixed(1)}x ({Math.round(baseSolar * solarMult).toLocaleString()} kWp)</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="2.5"
              step="0.1"
              value={solarMult}
              onChange={(e) => setSolarMult(parseFloat(e.target.value))}
              className="w-full accent-amber-500 bg-slate-800 rounded-lg h-2 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>0 kW</span>
              <span>{Math.round(baseSolar).toLocaleString()} kW</span>
              <span>{Math.round(baseSolar * 2.5).toLocaleString()} kW (2.5x)</span>
            </div>
          </div>

          {/* Slider 2: Battery Storage */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-slate-300 flex items-center gap-1.5">
                <BatteryCharging className="w-3.5 h-3.5 text-emerald-400" /> BESS Storage Size
              </span>
              <span className="font-bold text-emerald-400">{batteryMult.toFixed(1)}x ({Math.round(baseBattery * batteryMult).toLocaleString()} kWh)</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="2.5"
              step="0.1"
              value={batteryMult}
              onChange={(e) => setBatteryMult(parseFloat(e.target.value))}
              className="w-full accent-emerald-500 bg-slate-800 rounded-lg h-2 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>0 kWh</span>
              <span>{Math.round(baseBattery).toLocaleString()} kWh</span>
              <span>{Math.round(baseBattery * 2.5).toLocaleString()} kWh (2.5x)</span>
            </div>
          </div>

          {/* Slider 3: Grid Tariff Multiplier */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-slate-300 flex items-center gap-1.5">
                <DollarSign className="w-3.5 h-3.5 text-purple-400" /> Grid Tariff Rate
              </span>
              <span className="font-bold text-purple-400">{tariffMult.toFixed(2)}x Tariff Rate</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={tariffMult}
              onChange={(e) => setTariffMult(parseFloat(e.target.value))}
              className="w-full accent-purple-500 bg-slate-800 rounded-lg h-2 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>0.5x Subsidy</span>
              <span>1.0x Normal</span>
              <span>2.0x Peak Surge</span>
            </div>
          </div>

          {/* Slider 4: Weather Cloud Cover */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-slate-300 flex items-center gap-1.5">
                <CloudRain className="w-3.5 h-3.5 text-blue-400" /> Weather Cloud Cover
              </span>
              <span className="font-bold text-blue-400">{cloudCover.toFixed(0)}% Cover</span>
            </div>
            <input
              type="range"
              min="0"
              max="90"
              step="5"
              value={cloudCover}
              onChange={(e) => setCloudCover(parseFloat(e.target.value))}
              className="w-full accent-blue-500 bg-slate-800 rounded-lg h-2 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>0% (Clear Sky)</span>
              <span>50% (Scattered)</span>
              <span>90% (Monsoon)</span>
            </div>
          </div>

          {/* Toggle: Flexible Load Shifting */}
          <div className="pt-2 border-t border-slate-800">
            <label className="flex items-center justify-between text-xs text-slate-300 cursor-pointer">
              <span>Automate Flexible Load Shifting:</span>
              <input
                type="checkbox"
                checked={flexEnabled}
                onChange={(e) => setFlexEnabled(e.target.checked)}
                className="w-4 h-4 rounded bg-slate-800 border-slate-700 text-emerald-500 focus:ring-emerald-500 cursor-pointer"
              />
            </label>
          </div>
        </div>

        {/* Results & Comparison Metrics (2 Cols) */}
        <div className="lg:col-span-2 space-y-5">
          {/* Top Outcome Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl">
              <span className="text-xs text-slate-400 block">Daily Electricity Bill</span>
              <p className="text-xl font-extrabold text-white mt-1">
                ₹{simResult ? simResult.simulated_cost_inr.toLocaleString() : '---'}
              </p>
              <span className="text-[11px] text-emerald-400 flex items-center gap-1 mt-1">
                <TrendingDown className="w-3 h-3" />
                Savings: ₹{simResult ? simResult.savings_inr.toLocaleString() : '---'} ({simResult?.savings_percent}%)
              </span>
            </div>

            <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl">
              <span className="text-xs text-slate-400 block">Peak Grid Demand</span>
              <p className="text-xl font-extrabold text-cyan-400 mt-1">
                {simResult ? `${simResult.peak_grid_demand_kw.toLocaleString()} kW` : '---'}
              </p>
              <span className="text-[11px] text-slate-400 block mt-1">
                Shaved: {simResult?.peak_demand_shaved_kw ? `${simResult.peak_demand_shaved_kw} kW` : '0 kW'}
              </span>
            </div>

            <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl">
              <span className="text-xs text-slate-400 block">Solar Self-Consumption</span>
              <p className="text-xl font-extrabold text-amber-400 mt-1">
                {simResult ? `${simResult.solar_self_consumption_percent}%` : '---'}
              </p>
              <span className="text-[11px] text-slate-400 block mt-1">
                Gen: {simResult ? `${simResult.solar_generation_kwh.toLocaleString()} kWh` : '---'}
              </span>
            </div>

            <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl">
              <span className="text-xs text-slate-400 block">CO2 Avoided</span>
              <p className="text-xl font-extrabold text-emerald-400 mt-1">
                {simResult ? `${simResult.co2_avoided_tons} tons` : '---'}
              </p>
              <span className="text-[11px] text-slate-400 block mt-1">
                Residual: {simResult ? `${simResult.co2_emissions_tons} tons` : '---'}
              </span>
            </div>
          </div>

          {/* Explanation Text Card */}
          <div className="bg-gradient-to-r from-slate-900 via-slate-900/90 to-purple-950/20 border border-purple-500/30 p-5 rounded-2xl shadow-lg">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <h3 className="text-sm font-bold text-white">Simulation Narrative & Engineering Impact</h3>
            </div>
            <p className="text-xs text-slate-200 leading-relaxed font-medium">
              {simResult?.explanation || 'Simulating scenario metrics with the HiGHS linear solver...'}
            </p>
          </div>

          {/* Transparent Calculation Reference */}
          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Info className="w-3.5 h-3.5 text-blue-400" />
              Mathematical Formulas & Physical Rigor
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-slate-400 font-mono">
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80">
                <span className="text-amber-400 font-bold block mb-1">Solar Generation:</span>
                P_pv = Capacity * (GHI/1000) * (1 - 0.75*Cloud/100) * 0.94
              </div>
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80">
                <span className="text-emerald-400 font-bold block mb-1">Storage State of Charge:</span>
                SoC(t+1) = SoC(t) + (eta*P_ch - P_dis/eta) / Bat_Cap
              </div>
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80">
                <span className="text-blue-400 font-bold block mb-1">Grid Cost Balance:</span>
                Cost = sum( P_grid(t) * Tariff(t) ) + Demand_Charge
              </div>
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80">
                <span className="text-purple-400 font-bold block mb-1">Carbon Reduction:</span>
                CO2_Avoided = (Delta_Grid_kWh * 0.72 kg/kWh) / 1000
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
