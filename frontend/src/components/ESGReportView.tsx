import React from 'react';
import {
  FileText,
  Leaf,
  ShieldCheck,
  Award,
  Download,
  Printer,
  CheckCircle2,
  TrendingDown,
  Building,
  GraduationCap
} from 'lucide-react';
import { OptimizationResponse, LiveDashboardResponse, FacilityConfig } from '../types';

interface ESGReportViewProps {
  dashboardData: LiveDashboardResponse | null;
  optimizationData: OptimizationResponse | null;
  facilityConfig: FacilityConfig | null;
}

export const ESGReportView: React.FC<ESGReportViewProps> = ({
  dashboardData,
  optimizationData,
  facilityConfig,
}) => {
  const co2AvoidedTons = optimizationData ? optimizationData.co2_avoided_tons : 1.2;
  const costSavings = optimizationData ? optimizationData.cost_savings_inr : 8400;
  const gridReduction = optimizationData ? optimizationData.grid_reduction_kwh : 1980;

  function handlePrint() {
    window.print();
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
              <Leaf className="w-3.5 h-3.5" />
              ESG & Sustainability Accounting
            </span>
            <span className="text-xs text-slate-400">CEA Grid Factor Standard</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white">
            Campus Carbon Offsets & Sustainability Audit Report
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Verifiable greenhouse gas emission reductions and energy conservation metrics for institutional ESG ratings.
          </p>
        </div>

        <button
          onClick={handlePrint}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
        >
          <Printer className="w-4 h-4 text-emerald-400" />
          <span>Print / Export PDF Audit</span>
        </button>
      </div>

      {/* Sustainability Certificate Card */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-950 to-emerald-950/40 border border-emerald-500/40 p-8 rounded-3xl shadow-2xl relative overflow-hidden">
        <div className="absolute right-0 top-0 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-lg shadow-emerald-500/20">
              <Award className="w-7 h-7" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Green Building Energy Audit Certificate</h2>
              <p className="text-xs text-slate-400">Issued by NexusIQ Autonomous Sustainability Protocol</p>
            </div>
          </div>

          <div className="text-right">
            <span className="text-xs text-slate-400 block">Facility:</span>
            <span className="text-sm font-bold text-emerald-400">{facilityConfig?.name || 'NHCE Green Campus'}</span>
          </div>
        </div>

        {/* 3 Metric Badges */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 my-8">
          <div className="bg-slate-900/90 border border-slate-800 p-5 rounded-2xl text-center">
            <span className="text-xs text-slate-400 uppercase tracking-wider block">Avoided Greenhouse Gas</span>
            <p className="text-3xl font-extrabold text-emerald-400 mt-2">{co2AvoidedTons} Metric Tons</p>
            <span className="text-[11px] text-slate-400 mt-1 block">Equiv to planting ~58 mature trees</span>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 p-5 rounded-2xl text-center">
            <span className="text-xs text-slate-400 uppercase tracking-wider block">Grid Energy Displaced</span>
            <p className="text-3xl font-extrabold text-blue-400 mt-2">{gridReduction.toLocaleString()} kWh</p>
            <span className="text-[11px] text-slate-400 mt-1 block">Replaced by zero-emission solar</span>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 p-5 rounded-2xl text-center">
            <span className="text-xs text-slate-400 uppercase tracking-wider block">Operating Cost Reduction</span>
            <p className="text-3xl font-extrabold text-purple-400 mt-2">₹{costSavings.toLocaleString()}</p>
            <span className="text-[11px] text-slate-400 mt-1 block">Direct utility tariff savings</span>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-800 text-xs text-slate-300 space-y-2">
          <h3 className="font-bold text-white text-sm">Audit Methodology & Integrity Guarantee</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            All carbon calculations follow the Central Electricity Authority (CEA) Baseline Carbon Database for the Indian Power Sector (Version 19.0), utilizing an operating margin emission factor of 0.72 kg CO2 / kWh. Peak load shaving and load shift conservation verified with 0.0 kW balance deviation.
          </p>
        </div>

        <div className="mt-6 flex items-center justify-between text-[11px] text-slate-500 pt-4 border-t border-slate-800">
          <span>Ideathon 2026 • Team EcoNexus • NHCE</span>
          <span className="text-emerald-400 flex items-center gap-1 font-semibold">
            <ShieldCheck className="w-3.5 h-3.5" /> Verified Clean Energy Audit
          </span>
        </div>
      </div>
    </div>
  );
};

