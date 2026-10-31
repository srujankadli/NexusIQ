import React, { useState } from 'react';
import {
  Cpu,
  Zap,
  Download,
  CheckCircle2,
  Sparkles,
  Check,
  ShieldCheck,
  AlertCircle,
  BatteryCharging,
  ChevronDown,
  ChevronUp,
  Table,
  RefreshCw
} from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  AreaChart,
  Area,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  Legend
} from 'recharts';
import { OptimizationResponse, FacilityConfig } from '../types';
import { api } from '../services/api';

interface OptimizationViewProps {
  optimizationData: OptimizationResponse | null;
  facilityConfig: FacilityConfig | null;
  onRerunOptimization: (flexibleEnabled: boolean) => Promise<void>;
}

export const OptimizationView: React.FC<OptimizationViewProps> = ({
  optimizationData,
  facilityConfig,
  onRerunOptimization,
}) => {
  const [flexibleEnabled, setFlexibleEnabled] = useState(true);
  const [isRerunning, setIsRerunning] = useState(false);
  const [showTableInspector, setShowTableInspector] = useState(false);
  const [implementedRecs, setImplementedRecs] = useState<Record<string, boolean>>({
    'rec-flex-shift': true,
    'rec-battery-arbitrage': true,
    'rec-peak-shave': true,
  });

  const schedule = optimizationData?.schedule;
  const recommendations = optimizationData?.recommendations || [];
  const hasBattery = Boolean(facilityConfig?.has_battery && (facilityConfig?.battery_capacity_kwh ?? 0) > 0);

  // Error handling if data is missing or solver failed
  if (!optimizationData || !schedule) {
    return (
      <div className="space-y-6 pb-12">
        <div className="bg-rose-500/10 border border-rose-500/30 p-8 rounded-2xl text-center space-y-4">
          <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
          <h2 className="text-lg font-bold text-white">Optimization Dispatch Data Unavailable</h2>
          <p className="text-xs text-rose-200 max-w-lg mx-auto">
            The optimization engine has not returned a dispatch schedule or the server is initializing.
            Click below to trigger the HiGHS MILP optimization solver.
          </p>
          <button
            onClick={() => onRerunOptimization(flexibleEnabled)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl transition"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Run Energy Optimization</span>
          </button>
        </div>
      </div>
    );
  }

  // Map 24-hour dispatch data directly from backend fields without fabricated fallbacks
  const chartData = schedule.time_labels.map((time, idx) => ({
    time,
    hour: schedule.hours[idx],
    'Baseline Grid (kW)': schedule.baseline_grid_kw[idx] ?? 0,
    'Optimized Grid (kW)': schedule.optimized_grid_kw[idx] ?? 0,
    'Solar Utilized (kW)': schedule.solar_utilized_kw[idx] ?? 0,
    'Solar Surplus (kW)': schedule.solar_surplus_kw?.[idx] ?? 0,
    'Battery Charge (kW)': schedule.battery_charge_kw[idx] ?? 0,
    'Battery Discharge (kW)': schedule.battery_discharge_kw[idx] ?? 0,
    'Shifted Load (kW)': schedule.shifted_load_kw[idx] ?? 0,
    'Battery SoC (%)': schedule.battery_soc_percent[idx] ?? 0,
  }));

  async function handleToggleFlexible(enabled: boolean) {
    setFlexibleEnabled(enabled);
    setIsRerunning(true);
    try {
      await onRerunOptimization(enabled);
    } finally {
      setIsRerunning(false);
    }
  }

  function handleToggleRec(recId: string) {
    setImplementedRecs((prev) => ({
      ...prev,
      [recId]: !prev[recId],
    }));
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5" />
              HiGHS Mixed-Integer Linear Program (MILP)
            </span>
            <span className="text-xs text-slate-400">
              Execution Time: {optimizationData.computation_time_ms} ms
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white">
            Energy Dispatch Schedule & Storage Orchestration
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Co-optimizes solar utilization, battery arbitrage, controllable load shifts, and peak demand charges with 100% physical conservation.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => setShowTableInspector(!showTableInspector)}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition cursor-pointer"
          >
            <Table className="w-4 h-4 text-cyan-400" />
            <span>{showTableInspector ? 'Hide Data Table' : 'Inspect 24h Data'}</span>
          </button>

          <a
            href={api.getScheduleCsvUrl()}
            download="nexusiq_optimized_dispatch_schedule.csv"
            className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition cursor-pointer"
          >
            <Download className="w-4 h-4 text-emerald-400" />
            <span>Download Dispatch CSV</span>
          </a>

          <label className="flex items-center space-x-2 bg-slate-950 px-3.5 py-2 rounded-xl border border-slate-800 text-xs text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={flexibleEnabled}
              disabled={isRerunning}
              onChange={(e) => handleToggleFlexible(e.target.checked)}
              className="rounded bg-slate-900 border-slate-700 text-emerald-500 focus:ring-emerald-500"
            />
            <span>{isRerunning ? 'Solving...' : 'Flexible Load Shifting'}</span>
          </label>
        </div>
      </div>

      {/* Verified Status Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>{optimizationData.status_summary}</span>
        </div>
        <div className="flex items-center gap-4 text-[11px]">
          <span>Solar Capacity: <strong className="text-white">{facilityConfig?.has_solar ? `${facilityConfig.solar_installed_capacity_kw} kW` : 'None'}</strong></span>
          <span>BESS Storage: <strong className="text-white">{hasBattery ? `${facilityConfig?.battery_capacity_kwh} kWh (${facilityConfig?.battery_max_power_kw} kW)` : 'None'}</strong></span>
          <span>Contracted Grid: <strong className="text-white">{facilityConfig?.grid_contracted_demand_kw} kW</strong></span>
        </div>
      </div>

      {/* Metrics Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
          <div className="flex justify-between text-xs text-slate-400">
            <span>Daily Cost Saved</span>
            <span className="text-emerald-400 font-bold">-{optimizationData.cost_savings_percent}%</span>
          </div>
          <p className="text-2xl font-extrabold text-emerald-400 mt-2">
            ₹{optimizationData.cost_savings_inr.toLocaleString()}
          </p>
          <span className="text-[10px] text-slate-400 block mt-1">Tariff arbitrage & peak shaving</span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
          <div className="flex justify-between text-xs text-slate-400">
            <span>Peak Demand Shaved</span>
            <span className="text-blue-400 font-bold">kW Curtailment</span>
          </div>
          <p className="text-2xl font-extrabold text-blue-400 mt-2">
            {optimizationData.peak_demand_shaved_kw.toLocaleString()} kW
          </p>
          <span className="text-[10px] text-slate-400 block mt-1">Prevents utility demand penalty</span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
          <div className="flex justify-between text-xs text-slate-400">
            <span>Grid Import Reduction</span>
            <span className="text-amber-400 font-bold">Clean Energy</span>
          </div>
          <p className="text-2xl font-extrabold text-amber-400 mt-2">
            {optimizationData.grid_reduction_kwh.toLocaleString()} kWh
          </p>
          <span className="text-[10px] text-slate-400 block mt-1">Direct solar + battery dispatch</span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
          <div className="flex justify-between text-xs text-slate-400">
            <span>Avoided CO2</span>
            <span className="text-emerald-400 font-bold">CEA Grid Factor</span>
          </div>
          <p className="text-2xl font-extrabold text-emerald-400 mt-2">
            {optimizationData.co2_avoided_tons} tons
          </p>
          <span className="text-[10px] text-slate-400 block mt-1">0.72 kg CO2 / kWh baseline</span>
        </div>
      </div>

      {/* Transparent Financial Cost Breakdown */}
      <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl shadow">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
          Transparent Financial Objective & Cost Breakdown
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-slate-400 text-[10px] block">Energy Charges (ToU)</span>
            <p className="font-bold text-white mt-1">
              ₹{optimizationData.optimized_energy_cost_inr.toLocaleString()}
            </p>
            <span className="text-[10px] text-slate-500 block">Baseline: ₹{optimizationData.baseline_energy_cost_inr.toLocaleString()}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-slate-400 text-[10px] block">Contracted Demand Charge</span>
            <p className="font-bold text-cyan-400 mt-1">
              ₹{optimizationData.optimized_demand_charge_inr.toLocaleString()}
            </p>
            <span className="text-[10px] text-slate-500 block">Baseline: ₹{optimizationData.baseline_demand_charge_inr.toLocaleString()}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-slate-400 text-[10px] block">Battery Degradation Cost</span>
            <p className="font-bold text-purple-400 mt-1">
              ₹{optimizationData.battery_degradation_cost_inr.toLocaleString()}
            </p>
            <span className="text-[10px] text-slate-500 block">Throughput accounting</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-slate-400 text-[10px] block">Net Verified Daily Savings</span>
            <p className="font-bold text-emerald-400 mt-1">
              ₹{optimizationData.cost_savings_inr.toLocaleString()}
            </p>
            <span className="text-[10px] text-emerald-400 block font-medium">-{optimizationData.cost_savings_percent}% reduction</span>
          </div>
        </div>
      </div>

      {/* CHART 1: 24-Hour Dispatch & Power Flow (kW) */}
      <div className="bg-slate-900/90 border border-slate-800 p-6 rounded-2xl shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Zap className="w-4 h-4 text-emerald-400" />
              Optimal 24-Hour Dispatch & Power Flow Schedule
            </h2>
            <p className="text-xs text-slate-400">
              Coordinates grid imports, direct solar utilization, and battery charge/discharge to minimize utility costs.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 text-slate-400">
              <span className="w-2.5 h-2.5 bg-slate-500 rounded-sm" /> Baseline Grid
            </span>
            <span className="flex items-center gap-1.5 text-cyan-400">
              <span className="w-2.5 h-2.5 bg-cyan-500 rounded-sm" /> Optimized Grid
            </span>
            <span className="flex items-center gap-1.5 text-amber-400">
              <span className="w-2.5 h-2.5 bg-amber-500 rounded-sm" /> Solar Utilized
            </span>
            <span className="flex items-center gap-1.5 text-emerald-400">
              <span className="w-2.5 h-2.5 bg-emerald-500 rounded-sm" /> Battery Charge
            </span>
            <span className="flex items-center gap-1.5 text-rose-400">
              <span className="w-2.5 h-2.5 bg-rose-500 rounded-sm" /> Battery Discharge
            </span>
          </div>
        </div>

        <div className="h-80 w-full mt-3">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 15, left: -5, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} unit=" kW" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '8px',
                  fontSize: '12px',
                  color: '#f8fafc'
                }}
              />
              <Bar dataKey="Baseline Grid (kW)" fill="#475569" opacity={0.45} radius={[2, 2, 0, 0]} />
              <Bar dataKey="Optimized Grid (kW)" fill="#06b6d4" radius={[2, 2, 0, 0]} />
              <Bar dataKey="Battery Charge (kW)" fill="#10b981" radius={[2, 2, 0, 0]} />
              <Bar dataKey="Battery Discharge (kW)" fill="#f43f5e" radius={[2, 2, 0, 0]} />
              <Line
                type="monotone"
                dataKey="Solar Utilized (kW)"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* CHART 2: Dedicated Battery Storage & State of Charge (SoC) Trajectory */}
      <div className="bg-slate-900/90 border border-slate-800 p-6 rounded-2xl shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <BatteryCharging className="w-4 h-4 text-purple-400" />
              Battery Energy Storage System (BESS) SoC Trajectory
            </h2>
            <p className="text-xs text-slate-400">
              Tracks physical state-of-charge (0-100%) against minimum reserve (20%) and maximum ceiling (95%) limits.
            </p>
          </div>
          {hasBattery ? (
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1.5 text-purple-400">
                <span className="w-2.5 h-2.5 bg-purple-500 rounded-sm" /> Battery SoC (%)
              </span>
              <span className="flex items-center gap-1.5 text-amber-400">
                <span className="w-2 h-0.5 border-b border-dashed border-amber-400" /> Reserve Limit (20%)
              </span>
              <span className="flex items-center gap-1.5 text-emerald-400">
                <span className="w-2.5 h-2.5 bg-emerald-500 rounded-sm" /> Charge (kW)
              </span>
              <span className="flex items-center gap-1.5 text-rose-400">
                <span className="w-2.5 h-2.5 bg-rose-500 rounded-sm" /> Discharge (kW)
              </span>
            </div>
          ) : (
            <span className="text-xs px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
              No Storage Installed (Level 1/2)
            </span>
          )}
        </div>

        {hasBattery ? (
          <div className="h-64 w-full mt-3">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: -5, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis
                  yAxisId="soc"
                  domain={[0, 100]}
                  stroke="#a855f7"
                  tick={{ fontSize: 11 }}
                  unit="%"
                />
                <YAxis
                  yAxisId="power"
                  orientation="right"
                  stroke="#64748b"
                  tick={{ fontSize: 11 }}
                  unit=" kW"
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: '#f8fafc'
                  }}
                />
                <ReferenceLine
                  yAxisId="soc"
                  y={20}
                  stroke="#f59e0b"
                  strokeDasharray="4 4"
                  label={{ value: 'Min Reserve (20%)', fill: '#f59e0b', fontSize: 10, position: 'insideBottomLeft' }}
                />
                <ReferenceLine
                  yAxisId="soc"
                  y={95}
                  stroke="#3b82f6"
                  strokeDasharray="4 4"
                  label={{ value: 'Max Ceiling (95%)', fill: '#3b82f6', fontSize: 10, position: 'insideTopLeft' }}
                />
                <Bar
                  yAxisId="power"
                  dataKey="Battery Charge (kW)"
                  fill="#10b981"
                  opacity={0.8}
                  radius={[2, 2, 0, 0]}
                />
                <Bar
                  yAxisId="power"
                  dataKey="Battery Discharge (kW)"
                  fill="#f43f5e"
                  opacity={0.8}
                  radius={[2, 2, 0, 0]}
                />
                <Line
                  yAxisId="soc"
                  type="monotone"
                  dataKey="Battery SoC (%)"
                  stroke="#a855f7"
                  strokeWidth={2.5}
                  dot={{ r: 2, fill: '#a855f7' }}
                  activeDot={{ r: 5 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="p-8 rounded-xl bg-slate-950/60 border border-slate-800 text-center space-y-2">
            <p className="text-xs text-slate-400">
              Battery storage is disabled in this configuration. The platform is running pure flexible load coordination and solar self-consumption.
            </p>
            <p className="text-[11px] text-slate-500">
              Switch to <strong>Level 3 (Intelligent Campus)</strong> in the top bar to enable 1,200 kWh battery storage with ToU arbitrage.
            </p>
          </div>
        )}
      </div>

      {/* INSPECTOR: Collapsible 24-Hour Dispatch Numerical Data Table */}
      {showTableInspector && (
        <div className="bg-slate-900/90 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Table className="w-4 h-4 text-cyan-400" />
              24-Hour Dispatch Numerical Inspector (HiGHS MILP Output)
            </h3>
            <span className="text-[11px] text-slate-400">All units in kW unless specified</span>
          </div>

          <div className="overflow-x-auto max-h-96 rounded-xl border border-slate-800">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-950 text-slate-400 sticky top-0 border-b border-slate-800">
                <tr>
                  <th className="p-2.5">Time</th>
                  <th className="p-2.5">Baseline Grid</th>
                  <th className="p-2.5 text-cyan-400">Optimized Grid</th>
                  <th className="p-2.5 text-amber-400">Solar Gen</th>
                  <th className="p-2.5 text-emerald-400">Bat Charge</th>
                  <th className="p-2.5 text-rose-400">Bat Discharge</th>
                  <th className="p-2.5 text-purple-400">Bat SoC (%)</th>
                  <th className="p-2.5 text-blue-400">Flex Shift</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                {chartData.map((row) => (
                  <tr key={row.time} className="hover:bg-slate-800/40 transition">
                    <td className="p-2 text-white font-sans">{row.time}</td>
                    <td className="p-2 text-slate-400">{row['Baseline Grid (kW)'].toFixed(1)}</td>
                    <td className="p-2 text-cyan-300 font-semibold">{row['Optimized Grid (kW)'].toFixed(1)}</td>
                    <td className="p-2 text-amber-300">{row['Solar Utilized (kW)'].toFixed(1)}</td>
                    <td className="p-2 text-emerald-400">{row['Battery Charge (kW)'] > 0 ? row['Battery Charge (kW)'].toFixed(1) : '0.0'}</td>
                    <td className="p-2 text-rose-400">{row['Battery Discharge (kW)'] > 0 ? row['Battery Discharge (kW)'].toFixed(1) : '0.0'}</td>
                    <td className="p-2 text-purple-300">{row['Battery SoC (%)'].toFixed(1)}%</td>
                    <td className="p-2 text-blue-300">{row['Shifted Load (kW)'].toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Explainable Optimization Recommendations */}
      <div className="bg-slate-900/90 border border-slate-800 p-6 rounded-2xl shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-emerald-400" />
              Transparent, Explainable Optimization Recommendations ({recommendations.length})
            </h2>
            <p className="text-xs text-slate-400">
              Each recommendation provides physical reasoning, financial ₹ impact, energy shift, and operational bounds.
            </p>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
            Constraint-Guaranteed
          </span>
        </div>

        <div className="space-y-4">
          {recommendations.map((rec) => {
            const isImplemented = implementedRecs[rec.id] !== false;
            return (
              <div
                key={rec.id}
                className="bg-slate-950/70 border border-slate-800/90 hover:border-slate-700 p-5 rounded-xl transition flex flex-col md:flex-row md:items-start justify-between gap-4"
              >
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase">
                      {rec.category}
                    </span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 uppercase">
                      {rec.priority} Priority
                    </span>
                    <span className="text-[10px] text-slate-400">
                      {isImplemented ? '• Implemented in Dispatch Schedule' : '• Excluded by User'}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-white">{rec.title}</h3>
                  <p className="text-xs text-slate-300 leading-relaxed font-medium">{rec.reasoning}</p>

                  <div className="mt-3 p-3 rounded-lg bg-slate-900 border border-slate-800/80 text-xs space-y-1">
                    <div className="text-slate-300">
                      <strong className="text-emerald-400">Energy Impact: </strong>
                      {rec.energy_impact}
                    </div>
                    <div className="text-slate-300">
                      <strong className="text-cyan-400">Operational Guarantee: </strong>
                      {rec.operational_constraints}
                    </div>
                  </div>
                </div>

                <div className="flex flex-col sm:items-end justify-between self-stretch shrink-0 pt-1">
                  <div className="text-left sm:text-right">
                    <span className="text-[10px] text-slate-400 block uppercase font-medium">Daily Value</span>
                    <span className="text-xl font-extrabold text-emerald-400">
                      ₹{rec.financial_impact_inr.toLocaleString()}
                    </span>
                  </div>

                  <button
                    onClick={() => handleToggleRec(rec.id)}
                    className={`mt-4 sm:mt-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition cursor-pointer ${
                      isImplemented
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/30'
                        : 'bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700'
                    }`}
                  >
                    {isImplemented ? (
                      <>
                        <Check className="w-3.5 h-3.5" />
                        <span>Included</span>
                      </>
                    ) : (
                      <span>Excluded</span>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
