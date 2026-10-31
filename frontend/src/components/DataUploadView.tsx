import React, { useState } from 'react';
import {
  UploadCloud,
  FileText,
  Download,
  Sparkles,
  ArrowRight,
  FileCheck,
  AlertCircle,
  Database
} from 'lucide-react';
import { CSVUploadSummary } from '../types';
import { api } from '../services/api';

interface DataUploadViewProps {
  onUploadSuccess: (summary: CSVUploadSummary) => void;
  onNavigateToDashboard: () => void;
}

export const DataUploadView: React.FC<DataUploadViewProps> = ({
  onUploadSuccess,
  onNavigateToDashboard,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadSummary, setUploadSummary] = useState<CSVUploadSummary | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function handleUpload() {
    if (!file) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const summary = await api.uploadCSV(file);
      setUploadSummary(summary);
      onUploadSuccess(summary);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error parsing CSV file');
    } finally {
      setLoading(false);
    }
  }

  async function handleLoadSample() {
    setLoading(true);
    setErrorMsg(null);
    try {
      const summary = await api.loadSampleDataset();
      setUploadSummary(summary);
      onUploadSuccess(summary);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error loading sample dataset');
    } finally {
      setLoading(false);
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setErrorMsg(null);
    }
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/30 flex items-center gap-1.5">
              <UploadCloud className="w-3.5 h-3.5" />
              Deployment Level 1: Universal Data Ingestion
            </span>
            <span className="text-xs text-slate-400">Zero Hardware Required</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white">
            Ingest Electricity Bills or Smart Meter CSV Data
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Upload your raw utility bills or 15-minute interval smart-meter exports. NexusIQ automatically normalizes time-series data, detects baseload vampire leakage, and runs tariff optimization.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleLoadSample}
            disabled={loading}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600/90 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl shadow transition cursor-pointer"
          >
            <Database className="w-4 h-4" />
            <span>Load Demo Dataset (7 Days)</span>
          </button>
          <a
            href={api.getSampleCSVUrl()}
            download="nexusiq_sample_energy_data.csv"
            className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-xl border border-slate-700 transition cursor-pointer"
          >
            <Download className="w-4 h-4 text-emerald-400" />
            <span>Download CSV Template</span>
          </a>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Dropzone & Upload Action */}
        <div className="bg-slate-900/90 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-400" />
              File Uploader
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              Accepts CSV files with timestamps and demand columns (e.g. `demand_kw`, `kwh`, `solar_kw`).
            </p>

            {/* Drop Box */}
            <label className="border-2 border-dashed border-slate-700 hover:border-emerald-500/60 rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer bg-slate-950/50 hover:bg-slate-950/80 transition group">
              <UploadCloud className="w-10 h-10 text-slate-500 group-hover:text-emerald-400 mb-3 transition" />
              <span className="text-xs font-semibold text-slate-200 text-center">
                {file ? file.name : 'Click to select or drag & drop CSV file'}
              </span>
              <span className="text-[11px] text-slate-500 mt-1">
                {file ? `${(file.size / 1024).toFixed(1)} KB` : 'Supports standard utility billing and meter intervals'}
              </span>
              <input
                type="file"
                accept=".csv,.txt"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>

            {errorMsg && (
              <div className="mt-3 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}
          </div>

          <div className="mt-6 flex items-center justify-between pt-4 border-t border-slate-800">
            <span className="text-xs text-slate-400">
              Format: Interval or Monthly CSV
            </span>
            <button
              onClick={handleUpload}
              disabled={!file || loading}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold shadow-lg transition ${
                !file || loading
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/20 cursor-pointer'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{loading ? 'Processing...' : 'Parse & Profile Facility'}</span>
            </button>
          </div>
        </div>

        {/* Ingestion Results & Insights */}
        <div className="bg-slate-900/90 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <FileCheck className="w-4 h-4 text-emerald-400" />
                Ingestion Analysis Summary
              </span>
              {uploadSummary && (
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase">
                  {uploadSummary.detected_format}
                </span>
              )}
            </div>

            {uploadSummary ? (
              <div className="mt-4 space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                    <span className="text-slate-400 text-[10px] block">Total Logged Energy</span>
                    <span className="text-base font-bold text-white">
                      {uploadSummary.total_consumption_kwh.toLocaleString()} kWh
                    </span>
                    <span className="text-[10px] text-slate-500 block mt-0.5">{uploadSummary.total_records} records</span>
                  </div>
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                    <span className="text-slate-400 text-[10px] block">Peak Recorded Load</span>
                    <span className="text-base font-bold text-blue-400">
                      {uploadSummary.peak_recorded_demand_kw} kW
                    </span>
                    <span className="text-[10px] text-slate-500 block mt-0.5">Billing Demand Peak</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                    <span className="text-slate-400 text-[10px] block">Estimated Utility Bill</span>
                    <span className="text-base font-bold text-purple-400">
                      ₹{uploadSummary.estimated_bill_inr.toLocaleString()}
                    </span>
                    <span className="text-[10px] text-slate-500 block mt-0.5">Commercial Tariff Avg</span>
                  </div>
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                    <span className="text-slate-400 text-[10px] block">Baseload Leakage Identified</span>
                    <span className="text-base font-bold text-rose-400">
                      {uploadSummary.identified_wastage_kwh} kWh
                    </span>
                    <span className="text-[10px] text-emerald-400 block mt-0.5">
                      Potential: ₹{uploadSummary.identified_savings_potential_inr.toLocaleString()}
                    </span>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs">
                  <span className="font-semibold text-emerald-400 block mb-1">AI Recommendation</span>
                  <p className="text-slate-300 text-xs leading-relaxed">
                    {uploadSummary.recommendation_summary}
                  </p>
                </div>

                {uploadSummary.data_quality_notes && uploadSummary.data_quality_notes.length > 0 && (
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400 space-y-1">
                    <span className="font-semibold text-slate-300 block">Data Quality & Validation Audit:</span>
                    <ul className="list-disc pl-4 space-y-0.5">
                      {uploadSummary.data_quality_notes.map((note, i) => (
                        <li key={i}>{note}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-12 text-center text-slate-400 text-xs">
                <UploadCloud className="w-10 h-10 text-slate-600 mx-auto mb-2" />
                Upload a CSV file or click &ldquo;Load Demo Dataset&rdquo; above to see instant energy profiling and wastage analytics.
              </div>
            )}
          </div>

          {uploadSummary && (
            <div className="mt-5 pt-4 border-t border-slate-800 flex justify-end">
              <button
                onClick={onNavigateToDashboard}
                className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl shadow-lg transition cursor-pointer"
              >
                <span>View Live Dashboard with Uploaded Profile</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
