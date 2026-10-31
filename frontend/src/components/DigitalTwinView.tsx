import React, { useState, useEffect } from 'react';
import {
  Building2,
  Sun,
  BatteryCharging,
  Cpu,
  Layers,
  Thermometer,
  Users,
  Activity,
  CheckCircle2,
  Sliders,
  ShieldCheck,
  RefreshCw,
  Power
} from 'lucide-react';
import { BuildingLoad, EnergyFlowState, FacilityConfig } from '../types';
import { api } from '../services/api';

interface DigitalTwinViewProps {
  flowState: EnergyFlowState | null;
  facilityConfig: FacilityConfig | null;
  onTelemetryUpdated?: () => void;
}

export const DigitalTwinView: React.FC<DigitalTwinViewProps> = ({
  flowState,
  facilityConfig,
  onTelemetryUpdated,
}) => {
  const [buildings, setBuildings] = useState<BuildingLoad[]>([]);
  const [selectedBuilding, setSelectedBuilding] = useState<BuildingLoad | null>(null);
  const [shiftingId, setShiftingId] = useState<string | null>(null);
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  async function fetchBuildings() {
    try {
      const data = await api.getBuildings();
      setBuildings(data);
      if (!selectedBuilding && data.length > 0) {
        setSelectedBuilding(data[0]);
      } else if (selectedBuilding) {
        const found = data.find((b) => b.id === selectedBuilding.id);
        if (found) setSelectedBuilding(found);
      }
    } catch (err) {
      console.error(err);
    }
  }

  useEffect(() => {
    fetchBuildings();
  }, [facilityConfig?.level]);

  async function handleToggleShift(bld: BuildingLoad) {
    if (!bld.is_flexible) return;
    setShiftingId(bld.id);
    try {
      await api.toggleBuildingShift(bld.id);
      await fetchBuildings();
      if (onTelemetryUpdated) onTelemetryUpdated();
      setFeedbackMsg(`Load shift command dispatched to ${bld.name}. Submeter updated.`);
      setTimeout(() => setFeedbackMsg(null), 4000);
    } catch (err) {
      console.error(err);
    } finally {
      setShiftingId(null);
    }
  }

  const totalDemand = buildings.reduce((acc, b) => acc + b.current_load_kw, 0);
  const totalFlexible = buildings.reduce((acc, b) => acc + (b.is_flexible ? b.flexible_capacity_kw : 0), 0);

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              Campus Microgrid Digital Twin
            </span>
            <span className="text-xs text-slate-400">High-Resolution Physical Model</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white">
            NHCE Multi-Building Energy Flow & Sub-Meter Twin
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Simulates real-time energy flow dynamics across substation transformers, rooftop solar arrays, BESS storage, and 5 campus building clusters.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-right">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Total Submetered</span>
            <span className="text-lg font-bold text-indigo-400">{totalDemand.toLocaleString()} kW</span>
          </div>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-right">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Controllable Flexible</span>
            <span className="text-lg font-bold text-emerald-400">{totalFlexible.toLocaleString()} kW</span>
          </div>
        </div>
      </div>

      {feedbackMsg && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{feedbackMsg}</span>
        </div>
      )}

      {/* Main Schematic & Busbar Diagram */}
      <div className="bg-slate-900/90 border border-slate-800 p-6 rounded-2xl shadow-xl">
        <h2 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          Campus Electrical Busbar & Inverter Architecture
        </h2>

        {/* Busbar Layout */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-slate-950/80 p-5 rounded-xl border border-slate-800/80">
          {/* Node 1: Solar */}
          <div className="bg-slate-900/90 border border-amber-500/30 p-4 rounded-xl flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">Rooftop Solar PV Array</span>
              <Sun className="w-5 h-5 text-amber-400" />
            </div>
            <div className="my-3">
              <p className="text-2xl font-extrabold text-amber-400">
                {flowState ? `${(flowState.solar_generation_kw / 1000).toFixed(2)} MW` : '2.10 MW'}
              </p>
              <p className="text-[11px] text-slate-400">Installed: 2,100 kWp Polycrystalline</p>
            </div>
            <div className="pt-2 border-t border-slate-800 text-[11px] text-amber-300 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
              Direct MPPT Inverters Active
            </div>
          </div>

          {/* Node 2: Substation Grid */}
          <div className="bg-slate-900/90 border border-cyan-500/30 p-4 rounded-xl flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">11kV Main Utility Substation</span>
              <Cpu className="w-5 h-5 text-cyan-400" />
            </div>
            <div className="my-3">
              <p className="text-2xl font-extrabold text-cyan-400">
                {flowState ? `${(flowState.grid_consumption_kw / 1000).toFixed(2)} MW` : '1.98 MW'}
              </p>
              <p className="text-[11px] text-slate-400">Contracted: 6,000 kVA (BESCOM HT-2a)</p>
            </div>
            <div className="pt-2 border-t border-slate-800 text-[11px] text-cyan-300 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-cyan-400" />
              Within Contract Demand Ceiling
            </div>
          </div>

          {/* Node 3: BESS Storage */}
          <div className="bg-slate-900/90 border border-emerald-500/30 p-4 rounded-xl flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">Battery BESS (LiFePO4)</span>
              <BatteryCharging className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="my-3">
              <p className="text-2xl font-extrabold text-emerald-400">
                {flowState ? `${flowState.battery_soc_percent}% SoC` : '76% SoC'}
              </p>
              <p className="text-[11px] text-slate-400">Capacity: 1,200 kWh (800 kW max power)</p>
            </div>
            <div className="pt-2 border-t border-slate-800 text-[11px] text-emerald-300 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              {flowState && flowState.battery_flow_kw < 0 ? 'Charging from Solar Surplus' : 'Discharging for Peak Shaving'}
            </div>
          </div>

          {/* Node 4: Common 415V AC Bus */}
          <div className="bg-slate-900/90 border border-indigo-500/30 p-4 rounded-xl flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">Campus 415V Main Busbar</span>
              <Layers className="w-5 h-5 text-indigo-400" />
            </div>
            <div className="my-3">
              <p className="text-2xl font-extrabold text-indigo-400">
                {flowState ? `${(flowState.campus_demand_kw / 1000).toFixed(2)} MW` : '4.82 MW'}
              </p>
              <p className="text-[11px] text-slate-400">Frequency: 50.02 Hz | THD: 1.4%</p>
            </div>
            <div className="pt-2 border-t border-slate-800 text-[11px] text-indigo-300 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-indigo-400" />
              Total Energy Conserved (Δ = 0.0 kW)
            </div>
          </div>
        </div>
      </div>

      {/* Campus Buildings Grid & Detailed Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Buildings List (2 Cols) */}
        <div className="lg:col-span-2 space-y-3">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Building2 className="w-4 h-4 text-blue-400" />
            Campus Sub-Metered Buildings ({buildings.length})
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {buildings.map((bld) => {
              const isSelected = selectedBuilding?.id === bld.id;
              return (
                <div
                  key={bld.id}
                  onClick={() => setSelectedBuilding(bld)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-slate-800/90 border-emerald-500 shadow-md shadow-emerald-500/10'
                      : 'bg-slate-900/70 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
                        {bld.category}
                      </span>
                      <h3 className="text-sm font-bold text-white mt-2">{bld.name}</h3>
                    </div>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        bld.operational_status === 'Optimized'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : bld.operational_status === 'Shift Eligible'
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      }`}
                    >
                      {bld.operational_status}
                    </span>
                  </div>

                  <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                      <span className="text-slate-400 text-[10px] block">Current Load</span>
                      <span className="text-sm font-bold text-white">{bld.current_load_kw} kW</span>
                    </div>
                    <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                      <span className="text-slate-400 text-[10px] block">Flexible Margin</span>
                      <span className="text-sm font-bold text-emerald-400">
                        {bld.is_flexible ? `${bld.flexible_capacity_kw} kW` : 'Non-shiftable'}
                      </span>
                    </div>
                  </div>

                  <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/60">
                    <span className="flex items-center gap-1">
                      <Thermometer className="w-3 h-3 text-amber-400" />
                      {bld.temperature_c ? `${bld.temperature_c}°C` : 'Ambient'}
                    </span>
                    <span className="flex items-center gap-1">
                      <Users className="w-3 h-3 text-blue-400" />
                      {bld.occupancy_percent}% Occupancy
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Building Details Drawer */}
        <div className="bg-slate-900/90 border border-slate-800 p-5 rounded-2xl shadow-xl flex flex-col justify-between">
          {selectedBuilding ? (
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <span className="text-xs font-semibold text-emerald-400">Sub-Meter Node Telemetry</span>
                <span className="text-xs text-slate-400">{selectedBuilding.id}</span>
              </div>

              <h3 className="text-lg font-bold text-white mt-3">{selectedBuilding.name}</h3>
              <p className="text-xs text-slate-400 mt-1">
                Category: <strong className="text-slate-300">{selectedBuilding.category}</strong>
              </p>

              <div className="mt-5 space-y-3">
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Current Measured Demand:</span>
                    <span className="font-bold text-white">{selectedBuilding.current_load_kw} kW</span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full mt-2 overflow-hidden">
                    <div
                      className="bg-emerald-500 h-full rounded-full"
                      style={{ width: `${Math.min(100, (selectedBuilding.current_load_kw / selectedBuilding.peak_load_kw) * 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                    <span>Base: {selectedBuilding.base_load_kw} kW</span>
                    <span>Peak: {selectedBuilding.peak_load_kw} kW</span>
                  </div>
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Flexible Load Shifting:</span>
                    <span className="font-semibold text-emerald-400">
                      {selectedBuilding.is_flexible ? 'Enabled (AI Controlled)' : 'Critical / Fixed'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Controllable Capacity:</span>
                    <span className="font-bold text-white">{selectedBuilding.flexible_capacity_kw} kW</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Indoor Temp Setpoint:</span>
                    <span className="font-bold text-white">24.0°C (Measured: {selectedBuilding.temperature_c}°C)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Zone Occupancy:</span>
                    <span className="font-bold text-white">{selectedBuilding.occupancy_percent}%</span>
                  </div>
                </div>

                {/* Interactive Action Button */}
                {selectedBuilding.is_flexible && (
                  <button
                    onClick={() => handleToggleShift(selectedBuilding)}
                    disabled={shiftingId === selectedBuilding.id}
                    className="w-full mt-2 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-emerald-300 text-xs font-semibold border border-emerald-500/30 transition cursor-pointer"
                  >
                    <Power className="w-3.5 h-3.5 text-emerald-400" />
                    <span>
                      {selectedBuilding.operational_status === 'Optimized'
                        ? 'Revert to Baseline Schedule'
                        : `Simulate Shift of ${selectedBuilding.flexible_capacity_kw} kW Load`}
                    </span>
                  </button>
                )}
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-400">Select a building to view telemetry</p>
          )}

          <div className="mt-5 pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Refresh rate: 15-min interval</span>
            <span className="text-emerald-400 font-medium">BMS API Connected</span>
          </div>
        </div>
      </div>
    </div>
  );
};
