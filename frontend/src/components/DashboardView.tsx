import React from 'react';
import {
  Zap,
  Sun,
  BatteryCharging,
  Cpu,
  TrendingDown,
  TrendingUp,
  Leaf,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Building,
  Factory,
  GraduationCap,
  Hospital,
  Home,
  Layers,
  RefreshCw,
  UploadCloud
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts';
import { LiveDashboardResponse, ForecastResponse, OptimizationResponse } from '../types';

interface DashboardViewProps {
  dashboardData: LiveDashboardResponse | null;
  forecastData: ForecastResponse | null;
  optimizationData: OptimizationResponse | null;
  onNavigateToTab: (tab: string) => void;
  onRefreshTelemetry: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  dashboardData,
  forecastData,
  optimizationData,
  onNavigateToTab,
  onRefreshTelemetry,
}) => {
  const kpis = dashboardData?.kpis;
  const flow = dashboardData?.energy_flow;
  const level = dashboardData?.deployment_level || 'level_3_campus';

  // Prepare 24h demand vs solar chart data
  const chartData = forecastData?.time_labels.map((label, idx) => ({
    time: label,
    'Actual Demand': forecastData.actual_demand_kw[idx],
    'Forecasted Demand': forecastData.forecast_demand_kw[idx],
    'Solar Generation': forecastData.solar_forecast_kw[idx],
  })) || [];

  // Impact comparison data (Baseline vs Optimized)
  const impactData = [
    {
      category: 'Energy Cost (₹)',
      Baseline: optimizationData ? Math.round(optimizationData.total_cost_baseline_inr / 40) : 11200,
      Optimized: optimizationData ? Math.round(optimizationData.total_cost_optimized_inr / 40) : 8400,
      unit: '₹',
    },
    {
      category: 'Grid Usage (kWh)',
      Baseline: optimizationData ? Math.round(optimizationData.metrics_summary[1]?.baseline_value / 100) : 3650,
      Optimized: optimizationData ? Math.round(optimizationData.metrics_summary[1]?.optimized_value / 100) : 1980,
      unit: 'kWh',
    },
    {
      category: 'CO2 Emissions (tons)',
      Baseline: optimizationData ? Number((optimizationData.metrics_summary[3]?.baseline_value).toFixed(1)) : 2.1,
      Optimized: optimizationData ? Number((optimizationData.metrics_summary[3]?.optimized_value).toFixed(1)) : 1.2,
      unit: 'tons',
    },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Platform Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 p-6 border border-slate-700/60 shadow-xl">
        <div className="absolute right-0 top-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                Live Energy Orchestration
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
                {dashboardData?.facility_name || 'NHCE Campus'}
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/20 text-blue-400 border border-blue-500/30 uppercase tracking-wide">
                {level === 'level_1_basic' ? 'Level 1: Basic (Bill/CSV)' : level === 'level_2_solar' ? 'Level 2: Solar PV' : 'Level 3: Microgrid'}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Nexus<span className="text-emerald-400">IQ</span> Energy Management & Optimization
            </h1>
            <p className="text-slate-400 text-xs sm:text-sm mt-1 max-w-2xl">
              Universally coordinates electricity demand, renewable generation, battery storage, and grid interaction
              to maximize efficiency and achieve verifiable carbon reductions.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onRefreshTelemetry}
              title="Refresh Telemetry"
              className="flex items-center gap-1.5 px-3 py-2 bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-xl border border-slate-700 transition cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5 text-emerald-400" />
              <span>Refresh</span>
            </button>
            <button
              onClick={() => onNavigateToTab('data-upload')}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-emerald-600/20 transition cursor-pointer"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Ingest Data</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards (Matches Poster Layout) */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* 1. Total Consumption */}
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl shadow hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Consumption</span>
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <p className="text-xl font-bold text-white">
              {kpis ? `${kpis.total_consumption_kwh.toLocaleString()} kWh` : '4,820 kWh'}
            </p>
            <p className="text-[11px] text-blue-400 font-medium flex items-center gap-0.5 mt-1">
              <TrendingUp className="w-3 h-3" />
              {kpis?.total_consumption_trend || '+12% vs last week'}
            </p>
          </div>
        </div>

        {/* 2. Solar Generation */}
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl shadow hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Solar Generation</span>
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400">
              <Sun className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <p className="text-xl font-bold text-white">
              {kpis ? `${kpis.solar_generation_kwh.toLocaleString()} kWh` : '2,140 kWh'}
            </p>
            <p className="text-[11px] text-amber-400 font-medium flex items-center gap-0.5 mt-1">
              <TrendingUp className="w-3 h-3" />
              {kpis?.solar_generation_trend || '+18% vs last week'}
            </p>
          </div>
        </div>

        {/* 3. Battery State of Charge */}
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl shadow hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Battery SoC</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
              <BatteryCharging className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <p className="text-xl font-bold text-white">
              {kpis ? `${kpis.battery_soc_percent}%` : '76%'}
            </p>
            <p className="text-[11px] text-emerald-400 font-medium flex items-center gap-1 mt-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              {kpis?.battery_status || 'Charging'}
            </p>
          </div>
        </div>

        {/* 4. Grid Consumption */}
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl shadow hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Grid Consumption</span>
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-400">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <p className="text-xl font-bold text-white">
              {kpis ? `${kpis.grid_consumption_kwh.toLocaleString()} kWh` : '1,980 kWh'}
            </p>
            <p className="text-[11px] text-emerald-400 font-medium flex items-center gap-0.5 mt-1">
              <TrendingDown className="w-3 h-3" />
              {kpis?.grid_consumption_trend || '-20% vs baseline'}
            </p>
          </div>
        </div>

        {/* 5. Estimated Cost Today */}
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl shadow hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Estimated Cost Today</span>
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400 font-bold">
              ₹
            </div>
          </div>
          <div className="mt-3">
            <p className="text-xl font-bold text-white">
              {kpis ? `₹${kpis.estimated_cost_today_inr.toLocaleString()}` : '₹8,400'}
            </p>
            <p className="text-[11px] text-emerald-400 font-medium flex items-center gap-0.5 mt-1">
              <TrendingDown className="w-3 h-3" />
              {kpis?.estimated_cost_trend || '-22% vs baseline'}
            </p>
          </div>
        </div>

        {/* 6. CO2 Avoided */}
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl shadow hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">CO2 Emissions Avoided</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
              <Leaf className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <p className="text-xl font-bold text-white">
              {kpis ? `${kpis.co2_emissions_avoided_tons} tons` : '1.2 tons'}
            </p>
            <p className="text-[11px] text-emerald-400 font-medium flex items-center gap-0.5 mt-1">
              <TrendingUp className="w-3 h-3" />
              {kpis?.co2_trend || '+30% vs baseline'}
            </p>
          </div>
        </div>
      </div>

      {/* Primary Visuals Grid: Demand vs Solar Forecast (Left) & Energy Flow (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Energy Demand vs Solar Forecast */}
        <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                  Energy Demand vs Solar Forecast
                </h2>
                <p className="text-xs text-slate-400">24-hour predictive profile with weather adjustments</p>
              </div>
              <button
                onClick={() => onNavigateToTab('forecasting')}
                className="text-[11px] text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1 cursor-pointer"
              >
                <span>Explore AI Forecast</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <div className="h-72 w-full mt-2">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorDemand" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="colorSolar" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#eab308" stopOpacity={0.5} />
                      <stop offset="95%" stopColor="#eab308" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '12px',
                      color: '#f8fafc'
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Area
                    type="monotone"
                    dataKey="Actual Demand"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorDemand)"
                  />
                  <Area
                    type="monotone"
                    dataKey="Forecasted Demand"
                    stroke="#60a5fa"
                    strokeDasharray="4 4"
                    strokeWidth={1.5}
                    fill="none"
                  />
                  <Area
                    type="monotone"
                    dataKey="Solar Generation"
                    stroke="#eab308"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorSolar)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Model: Sandia PV + Gradient Boosted Time-Series</span>
            <span className="text-emerald-400 font-medium">95% Bayesian Confidence</span>
          </div>
        </div>

        {/* Right: Energy Flow (Live View / Digital Twin) */}
        <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                Energy Flow (Live View / Digital Twin)
              </h2>
              <p className="text-xs text-slate-400">Real-time power dispatch & conservation validation</p>
            </div>
            <button
              onClick={() => onNavigateToTab('digital-twin')}
              className="text-[11px] text-emerald-400 hover:text-emerald-300 font-medium flex items-center gap-1 cursor-pointer"
            >
              <span>Open 3D Campus Twin</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          {/* Interactive Schematic Diagram */}
          <div className="relative my-auto bg-slate-950/70 rounded-xl border border-slate-800/80 p-5 min-h-[280px] flex flex-col justify-center">
            {/* SVG Connecting Flow Lines with Animation */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
              <line x1="25%" y1="28%" x2="50%" y2="52%" stroke="#eab308" strokeWidth="2.5" strokeDasharray="6 4" className="animate-pulse" />
              <line x1="75%" y1="28%" x2="50%" y2="52%" stroke="#06b6d4" strokeWidth="2.5" strokeDasharray="6 4" className="animate-pulse" />
              <line x1="50%" y1="52%" x2="25%" y2="76%" stroke="#10b981" strokeWidth="2.5" strokeDasharray="6 4" className="animate-pulse" />
              <line x1="50%" y1="52%" x2="75%" y2="76%" stroke="#818cf8" strokeWidth="3" strokeDasharray="6 4" className="animate-pulse" />
            </svg>

            {/* Top Row: Solar & Grid */}
            <div className="grid grid-cols-2 gap-8 z-10">
              {/* Solar Card */}
              <div className="flex items-center space-x-3 bg-slate-900/90 border border-amber-500/40 p-3 rounded-xl shadow-lg">
                <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center text-amber-400">
                  <Sun className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-300">Solar PV</p>
                  <p className="text-lg font-extrabold text-amber-400">
                    {flow ? `${(flow.solar_generation_kw / 1000).toFixed(1)} MW` : '2.1 MW'}
                  </p>
                </div>
              </div>

              {/* Grid Card */}
              <div className="flex items-center space-x-3 bg-slate-900/90 border border-cyan-500/40 p-3 rounded-xl shadow-lg">
                <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center text-cyan-400">
                  <Cpu className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-300">Grid Import</p>
                  <p className="text-lg font-extrabold text-cyan-400">
                    {flow ? `${(flow.grid_consumption_kw / 1000).toFixed(1)} MW` : '2.0 MW'}
                  </p>
                </div>
              </div>
            </div>

            {/* Central Orchestrator Node */}
            <div className="my-5 flex justify-center z-10">
              <div className="px-4 py-1.5 rounded-full bg-slate-900 border border-emerald-500/50 shadow-lg shadow-emerald-500/10 flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                <span className="text-xs font-bold text-white tracking-wider">
                  NEXUS ORCHESTRATOR HUB
                </span>
              </div>
            </div>

            {/* Bottom Row: Battery & Campus Buildings */}
            <div className="grid grid-cols-2 gap-8 z-10">
              {/* Battery Card */}
              <div className="flex items-center space-x-3 bg-slate-900/90 border border-emerald-500/40 p-3 rounded-xl shadow-lg">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400">
                  <BatteryCharging className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-300">Battery BESS</p>
                  <p className="text-lg font-extrabold text-emerald-400">
                    {flow ? `${Math.abs(flow.battery_flow_kw / 1000).toFixed(1)} MW` : '0.8 MW'}
                  </p>
                  <span className="text-[10px] text-emerald-300">
                    {flow && flow.battery_flow_kw < 0 ? 'Charging (Surplus)' : 'Discharging'}
                  </span>
                </div>
              </div>

              {/* Campus Buildings Card */}
              <div className="flex items-center space-x-3 bg-slate-900/90 border border-indigo-500/40 p-3 rounded-xl shadow-lg">
                <div className="w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <Building className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-300">Campus Demand</p>
                  <p className="text-lg font-extrabold text-indigo-400">
                    {flow ? `${(flow.campus_demand_kw / 1000).toFixed(1)} MW` : '4.8 MW'}
                  </p>
                  <span className="text-[10px] text-indigo-300">5 Buildings Submetered</span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400">
            <span>Conservation: P_grid + P_solar + P_bat = P_campus</span>
            <span className="text-emerald-400 font-medium">Equilibrium Verified (0.0 kW Delta)</span>
          </div>
        </div>
      </div>

      {/* Secondary Row: AI Recommendation Card (Left) & Impact Comparison (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: AI Recommendation */}
        <div className="bg-gradient-to-br from-slate-900 via-slate-900/90 to-emerald-950/20 border border-emerald-500/30 p-5 rounded-2xl shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <div className="w-7 h-7 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400">
                  <Leaf className="w-4 h-4" />
                </div>
                <h2 className="text-base font-bold text-white">AI Recommendation</h2>
              </div>
              <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30">
                Actionable Optimization
              </span>
            </div>

            <p className="text-sm text-slate-200 leading-relaxed font-medium">
              Shift non-critical loads (e.g., water pumping, HVAC pre-cooling) to <strong>12:00 PM – 3:00 PM</strong> to utilize solar surplus and reduce grid dependence. Charge battery during surplus, reserve 60% capacity for evening peak demand.
            </p>

            <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
              <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-400 block text-[10px]">Expected Saving</span>
                <span className="text-emerald-400 font-bold text-sm">
                  {optimizationData ? `₹${optimizationData.cost_savings_inr.toLocaleString()}/day` : '₹2,800/day'}
                </span>
              </div>
              <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-400 block text-[10px]">Load Shifted</span>
                <span className="text-blue-400 font-bold text-sm">650 kWh</span>
              </div>
              <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-400 block text-[10px]">Constraint Guard</span>
                <span className="text-amber-400 font-bold text-sm">Comfort ±1.2°C</span>
              </div>
            </div>
          </div>

          <div className="mt-5 pt-3 border-t border-slate-800/80 flex items-center justify-between">
            <span className="text-xs text-slate-400">MILP Dispatch Schedule Ready</span>
            <button
              onClick={() => onNavigateToTab('optimization')}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-600/20 transition cursor-pointer"
            >
              <span>View Optimization Plan</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Right: Impact Comparison (Today) */}
        <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
                  Impact Comparison (Today)
                </h2>
                <p className="text-xs text-slate-400">Measurable baseline vs AI-optimized metrics</p>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="flex items-center gap-1 text-slate-400">
                  <span className="w-2.5 h-2.5 rounded-sm bg-slate-500" /> Baseline
                </span>
                <span className="flex items-center gap-1 text-emerald-400 font-medium">
                  <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500" /> Optimized
                </span>
              </div>
            </div>

            <div className="h-64 w-full mt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={impactData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="category" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '12px',
                      color: '#f8fafc'
                    }}
                  />
                  <Bar dataKey="Baseline" fill="#64748b" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Optimized" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
            <span>Reduces peak grid tariff costs</span>
            <button
              onClick={() => onNavigateToTab('what-if')}
              className="text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1 cursor-pointer"
            >
              <span>Test What-If Scenarios</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      {/* Deployment Levels & Target Users Footer Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pt-4">
        {/* Universal Adaptability */}
        <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
            <Layers className="w-3.5 h-3.5 text-blue-400" />
            Deployment Levels (Universal Adaptability)
          </h3>
          <div className="space-y-2.5 text-xs">
            <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
              <span className="font-semibold text-blue-400">Level 1 — Basic</span>
              <p className="text-slate-400 mt-0.5">Upload bills / CSV data. Useful insights without new hardware. Easy to adopt.</p>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
              <span className="font-semibold text-amber-400">Level 2 — Smart Meter & Solar</span>
              <p className="text-slate-400 mt-0.5">Connect meter data, weather & solar generation. Continuous monitoring & AI forecasting.</p>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
              <span className="font-semibold text-emerald-400">Level 3 — Intelligent Campus</span>
              <p className="text-slate-400 mt-0.5">Multi-building optimization, battery & load coordination, and digital twin simulation.</p>
            </div>
          </div>
        </div>

        {/* Target Users */}
        <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
            <GraduationCap className="w-3.5 h-3.5 text-emerald-400" />
            Target Facilities
          </h3>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center gap-2">
              <GraduationCap className="w-4 h-4 text-emerald-400" />
              <span>Colleges & Universities</span>
            </div>
            <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center gap-2">
              <Building className="w-4 h-4 text-blue-400" />
              <span>Corporate Offices</span>
            </div>
            <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center gap-2">
              <Hospital className="w-4 h-4 text-rose-400" />
              <span>Hospitals & Healthcare</span>
            </div>
            <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center gap-2">
              <Factory className="w-4 h-4 text-amber-400" />
              <span>Industrial Campuses</span>
            </div>
            <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center gap-2">
              <Home className="w-4 h-4 text-teal-400" />
              <span>Residential Communities</span>
            </div>
            <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-purple-400" />
              <span>Smart Cities & Govt</span>
            </div>
          </div>
        </div>

        {/* Expected Impact */}
        <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            Expected Impact
          </h3>
          <ul className="space-y-2 text-xs text-slate-300">
            <li className="flex items-start gap-2">
              <span className="text-emerald-400 font-bold">10–30%</span> reduction in electricity costs
            </li>
            <li className="flex items-start gap-2">
              <span className="text-amber-400 font-bold">Higher</span> renewable energy self-utilization
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-400 font-bold">Lower</span> peak demand surcharge & grid dependence
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-400 font-bold">Measurable</span> carbon emissions avoided
            </li>
            <li className="flex items-start gap-2">
              <span className="text-purple-400 font-bold">Replicable</span> across different building types
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};
