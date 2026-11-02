import React, { useState } from 'react';
import {
  Sparkles,
  Sun,
  CloudSun,
  Thermometer,
  Zap,
  Cpu,
  CheckCircle2,
  ShieldAlert,
  ArrowRight,
  Wrench
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import { ForecastResponse } from '../types';
import { api } from '../services/api';

interface ForecastingViewProps {
  forecastData: ForecastResponse | null;
  onRefreshForecast: (cloudCover: number) => Promise<void>;
}

export const ForecastingView: React.FC<ForecastingViewProps> = ({ forecastData, onRefreshForecast }) => {
  const weather = forecastData?.weather_summary;
  const metadata = forecastData?.model_metadata;
  const anomalies = forecastData?.anomalies || [];

  const [activeWeather, setActiveWeather] = useState(weather?.cloud_cover_percent || 15);
  const [remediatingId, setRemediatingId] = useState<string | null>(null);
  const [remediatedMsg, setRemediatedMsg] = useState<string | null>(null);

  const chartData = forecastData?.time_labels.map((label, idx) => ({
    time: label,
    'Forecast Demand (kW)': forecastData.forecast_demand_kw[idx],
    'Demand Upper (95%)': forecastData.demand_upper_bound_kw[idx],
    'Demand Lower (95%)': forecastData.demand_lower_bound_kw[idx],
    'Actual Measured (kW)': forecastData.actual_demand_kw[idx],
    'Solar Generation (kW)': forecastData.solar_forecast_kw[idx],
  })) || [];

  async function handleWeatherChange(val: number) {
    setActiveWeather(val);
    await onRefreshForecast(val);
  }

  async function handleRemediate(anomalyId: string, title: string) {
    setRemediatingId(anomalyId);
    try {
      await api.remediateAnomaly(anomalyId);
      await onRefreshForecast(activeWeather);
      setRemediatedMsg(`Anomaly "${title}" successfully remediated via automated BMS interlock.`);
      setTimeout(() => setRemediatedMsg(null), 5000);
    } catch (err) {
      console.error(err);
    } finally {
      setRemediatingId(null);
    }
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/30 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-blue-400" />
              Machine Learning Demand & Sandia PV Model
            </span>
            <span className="text-xs text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
              R²: <strong className="text-blue-400">{metadata?.r2_score_demand ?? '---'}</strong>
            </span>
            <span className="text-xs text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
              MAE: <strong className="text-emerald-400">{metadata?.mae_kw !== undefined ? `${metadata.mae_kw} kW` : '---'}</strong>
            </span>
            <span className="text-xs text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
              RMSE: <strong className="text-purple-400">{metadata?.rmse_kw !== undefined ? `${metadata.rmse_kw} kW` : '---'}</strong>
            </span>
            <span className="text-xs text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
              MAPE: <strong className="text-amber-400">{metadata?.mape_percent !== undefined ? `${metadata.mape_percent}%` : '---'}</strong>
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white">
            AI Demand Prediction & Solar Generation Modeling
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Decoupled architecture: Ridge regression trained on historical degree-day features paired with physical Sandia clear-sky optical PV modeling.
          </p>
        </div>

        {/* Weather Simulator Buttons */}
        <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
          {[
            { label: 'Clear Sky (10%)', val: 10 },
            { label: 'Scattered (25%)', val: 25 },
            { label: 'Overcast (60%)', val: 60 },
            { label: 'Monsoon (85%)', val: 85 },
          ].map((w) => (
            <button
              key={w.label}
              onClick={() => handleWeatherChange(w.val)}
              className={`px-3 py-1.5 rounded-lg font-medium transition cursor-pointer ${
                activeWeather === w.val
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {w.label}
            </button>
          ))}
        </div>
      </div>

      {remediatedMsg && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{remediatedMsg}</span>
        </div>
      )}

      {/* Weather Factors Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400">
            <Sun className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-400">Peak GHI Irradiance</p>
            <p className="text-lg font-bold text-white">{weather?.peak_irradiance_w_m2 || 940} W/m²</p>
            <span className="text-[10px] text-amber-400">Clear Sky Model</span>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400">
            <CloudSun className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-400">Cloud Cover Index</p>
            <p className="text-lg font-bold text-white">{weather?.cloud_cover_percent || 15}%</p>
            <span className="text-[10px] text-blue-400">{weather?.condition || 'Partly Sunny'}</span>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-rose-500/10 flex items-center justify-center text-rose-400">
            <Thermometer className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-400">Campus Ambient Temp</p>
            <p className="text-lg font-bold text-white">{weather?.avg_temperature_c || 26.5}°C</p>
            <span className="text-[10px] text-rose-400">Max: {weather?.max_temperature_c || 32.0}°C</span>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-400">HVAC Thermal Impact</p>
            <p className="text-lg font-bold text-white">+{weather?.cooling_degree_impact_percent || 12.4}%</p>
            <span className="text-[10px] text-purple-400">+3.8% demand / °C above 24°C</span>
          </div>
        </div>
      </div>

      {/* Primary Forecast Chart */}
      <div className="bg-slate-900/90 border border-slate-800 p-6 rounded-2xl shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Zap className="w-4 h-4 text-emerald-400" />
              24-Hour Predictive Energy Demand & Solar PV Generation
            </h2>
            <p className="text-xs text-slate-400">
              Shaded bounds indicate 95% Bayesian confidence intervals based on weather variation.
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 text-blue-400 font-medium">
              <span className="w-3 h-0.5 bg-blue-500" /> Forecast Demand
            </span>
            <span className="flex items-center gap-1.5 text-amber-400 font-medium">
              <span className="w-3 h-0.5 bg-amber-500" /> Solar PV
            </span>
            <span className="flex items-center gap-1.5 text-slate-300 font-medium">
              <span className="w-3 h-0.5 bg-slate-400 stroke-dash" /> Actual Measured
            </span>
          </div>
        </div>

        <div className="h-80 w-full mt-3">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="foreDemandGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="foreSolarGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#eab308" stopOpacity={0.4} />
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
              <Area
                type="monotone"
                dataKey="Forecast Demand (kW)"
                stroke="#3b82f6"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#foreDemandGrad)"
              />
              <Area
                type="monotone"
                dataKey="Solar Generation (kW)"
                stroke="#eab308"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#foreSolarGrad)"
              />
              <Line
                type="monotone"
                dataKey="Actual Measured (kW)"
                stroke="#94a3b8"
                strokeWidth={1.5}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="Demand Upper (95%)"
                stroke="#3b82f6"
                strokeDasharray="2 2"
                strokeWidth={1}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="Demand Lower (95%)"
                stroke="#3b82f6"
                strokeDasharray="2 2"
                strokeWidth={1}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* AI Anomaly Detection & Wastage Identification Section */}
      <div className="bg-slate-900/90 border border-slate-800 p-6 rounded-2xl shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-rose-400" />
              Automated Anomaly Detection & Baseload Wastage Alerts
            </h2>
            <p className="text-xs text-slate-400">
              Identifies energy leakage, vampire loads, and uncoordinated equipment operation in real time.
            </p>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-semibold">
            {anomalies.length} Flagged Events
          </span>
        </div>

        {anomalies.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-xs">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
            No active energy anomalies detected. All campus zones operating within nominal baselines.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {anomalies.map((anom) => (
              <div
                key={anom.id}
                className="bg-slate-950/70 border border-slate-800 hover:border-slate-700 p-4 rounded-xl flex flex-col justify-between transition"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-700">
                      {anom.timestamp} • {anom.anomaly_type}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                        anom.severity === 'high'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      }`}
                    >
                      {anom.severity} Severity
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-white">{anom.title}</h3>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">{anom.description}</p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="text-xs">
                    <span className="text-slate-400 text-[10px] block">Wasted Energy / Cost</span>
                    <span className="text-rose-400 font-bold">
                      +{anom.excess_kwh} kWh (₹{anom.estimated_waste_cost_inr.toLocaleString()})
                    </span>
                  </div>
                  <button
                    onClick={() => handleRemediate(anom.id, anom.title)}
                    disabled={remediatingId === anom.id}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/90 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition cursor-pointer"
                  >
                    <Wrench className="w-3.5 h-3.5" />
                    <span>{remediatingId === anom.id ? 'Remediating...' : 'Execute Remediation'}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
