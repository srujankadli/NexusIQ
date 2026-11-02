import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { DashboardView } from './components/DashboardView';
import { DigitalTwinView } from './components/DigitalTwinView';
import { ForecastingView } from './components/ForecastingView';
import { OptimizationView } from './components/OptimizationView';
import { WhatIfSimulatorView } from './components/WhatIfSimulatorView';
import { DataUploadView } from './components/DataUploadView';
import { ESGReportView } from './components/ESGReportView';
import { SettingsModal } from './components/SettingsModal';
import {
  DeploymentLevel,
  FacilityConfig,
  LiveDashboardResponse,
  ForecastResponse,
  OptimizationResponse,
  CSVUploadSummary
} from './types';
import { api } from './services/api';
import { CheckCircle2, RefreshCw } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [facilityConfig, setFacilityConfig] = useState<FacilityConfig | null>(null);
  const [dashboardData, setDashboardData] = useState<LiveDashboardResponse | null>(null);
  const [forecastData, setForecastData] = useState<ForecastResponse | null>(null);
  const [optimizationData, setOptimizationData] = useState<OptimizationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusNotification, setStatusNotification] = useState<string | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  async function loadData() {
    setLoading(true);
    try {
      const [cfgRes, dashRes, fcRes, optRes] = await Promise.allSettled([
        api.getProfile(),
        api.getLiveDashboard(),
        api.getForecast(15),
        api.runOptimization(true),
      ]);
      if (cfgRes.status === 'fulfilled') setFacilityConfig(cfgRes.value);
      if (dashRes.status === 'fulfilled') setDashboardData(dashRes.value);
      if (fcRes.status === 'fulfilled') setForecastData(fcRes.value);
      if (optRes.status === 'fulfilled') setOptimizationData(optRes.value);
    } catch (err) {
      console.error('Failed to load platform data:', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleRefreshTelemetry() {
    try {
      setLoading(true);
      const [dashRes, fcRes, optRes] = await Promise.allSettled([
        api.getLiveDashboard(),
        api.getForecast(15),
        api.runOptimization(true),
      ]);
      if (dashRes.status === 'fulfilled') setDashboardData(dashRes.value);
      if (fcRes.status === 'fulfilled') setForecastData(fcRes.value);
      if (optRes.status === 'fulfilled') setOptimizationData(optRes.value);
      setStatusNotification('Live telemetry and energy flow recalculated.');
      setTimeout(() => setStatusNotification(null), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSwitchLevel(level: DeploymentLevel) {
    try {
      setLoading(true);
      const newConfig = await api.switchLevel(level);
      setFacilityConfig(newConfig);

      const [dashRes, fcRes, optRes] = await Promise.allSettled([
        api.getLiveDashboard(),
        api.getForecast(15),
        api.runOptimization(true),
      ]);
      if (dashRes.status === 'fulfilled') setDashboardData(dashRes.value);
      if (fcRes.status === 'fulfilled') setForecastData(fcRes.value);
      if (optRes.status === 'fulfilled') setOptimizationData(optRes.value);

      const levelLabels = {
        level_1_basic: 'Level 1: Basic (Only Bills / CSV Data, No Solar, No Battery)',
        level_2_solar: 'Level 2: Smart Meter & Solar PV (No Battery)',
        level_3_campus: 'Level 3: Intelligent Campus (Solar + BESS + Digital Twin)',
      };
      setStatusNotification(`Switched deployment to ${levelLabels[level]}`);
      setTimeout(() => setStatusNotification(null), 5000);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveSettings(updated: FacilityConfig) {
    const saved = await api.updateSettings(updated);
    setFacilityConfig(saved);
    await handleRefreshTelemetry();
    setStatusNotification('Facility parameters and tariffs updated.');
    setTimeout(() => setStatusNotification(null), 4000);
  }

  async function handleSwitchMode(mode: 'demo' | 'uploaded') {
    try {
      setLoading(true);
      await api.switchDatasetMode(mode);
      const [cfgRes, dashRes, fcRes, optRes] = await Promise.allSettled([
        api.getProfile(),
        api.getLiveDashboard(),
        api.getForecast(15),
        api.runOptimization(true),
      ]);
      if (cfgRes.status === 'fulfilled') setFacilityConfig(cfgRes.value);
      if (dashRes.status === 'fulfilled') setDashboardData(dashRes.value);
      if (fcRes.status === 'fulfilled') setForecastData(fcRes.value);
      if (optRes.status === 'fulfilled') setOptimizationData(optRes.value);
      setStatusNotification(
        mode === 'demo'
          ? 'Switched to Demo Benchmark Mode (Synthetic NHCE Campus).'
          : 'Restored active uploaded dataset.'
      );
      setTimeout(() => setStatusNotification(null), 5000);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleUploadSuccess(summary: CSVUploadSummary) {
    setLoading(true);
    setStatusNotification(
      `Dataset Activated: "${summary.filename}" (${summary.total_records} intervals). Total: ${summary.total_consumption_kwh.toLocaleString()} kWh, Peak: ${summary.peak_recorded_demand_kw} kW.`
    );
    try {
      const [cfgRes, dashRes, fcRes, optRes] = await Promise.allSettled([
        api.getProfile(),
        api.getLiveDashboard(),
        api.getForecast(15),
        api.runOptimization(true),
      ]);
      if (cfgRes.status === 'fulfilled') setFacilityConfig(cfgRes.value);
      if (dashRes.status === 'fulfilled') setDashboardData(dashRes.value);
      if (fcRes.status === 'fulfilled') setForecastData(fcRes.value);
      if (optRes.status === 'fulfilled') setOptimizationData(optRes.value);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
      setTimeout(() => setStatusNotification(null), 6000);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        facilityConfig={facilityConfig}
        activeDataset={dashboardData?.active_dataset || null}
        onSwitchLevel={handleSwitchLevel}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onSwitchMode={handleSwitchMode}
      />

      {/* Notification Toast */}
      {statusNotification && (
        <div className="bg-emerald-500/10 border-b border-emerald-500/30 text-emerald-300 text-xs py-2 px-4 flex items-center justify-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{statusNotification}</span>
        </div>
      )}

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {loading && !dashboardData ? (
          <div className="py-24 flex flex-col items-center justify-center space-y-4">
            <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin" />
            <p className="text-sm text-slate-400 font-medium">
              Initializing NexusIQ Energy Orchestration Engine...
            </p>
          </div>
        ) : (
          <>
            {activeTab === 'dashboard' && (
              <DashboardView
                dashboardData={dashboardData}
                forecastData={forecastData}
                optimizationData={optimizationData}
                onNavigateToTab={(tab) => setActiveTab(tab)}
                onRefreshTelemetry={handleRefreshTelemetry}
                isLoading={loading}
              />
            )}

            {activeTab === 'digital-twin' && (
              <DigitalTwinView
                flowState={dashboardData?.energy_flow || null}
                facilityConfig={facilityConfig}
                onTelemetryUpdated={handleRefreshTelemetry}
              />
            )}

            {activeTab === 'forecasting' && (
              <ForecastingView
                forecastData={forecastData}
                onRefreshForecast={async (cloud) => {
                  const fc = await api.getForecast(cloud);
                  setForecastData(fc);
                }}
              />
            )}

            {activeTab === 'optimization' && (
              <OptimizationView
                optimizationData={optimizationData}
                facilityConfig={facilityConfig}
                onRerunOptimization={async (flex) => {
                  const opt = await api.runOptimization(flex);
                  setOptimizationData(opt);
                }}
              />
            )}

            {activeTab === 'what-if' && (
              <WhatIfSimulatorView
                facilityConfig={facilityConfig}
                onApplyConfig={handleSaveSettings}
              />
            )}

            {activeTab === 'data-upload' && (
              <DataUploadView
                onUploadSuccess={handleUploadSuccess}
                onNavigateToDashboard={() => setActiveTab('dashboard')}
              />
            )}

            {activeTab === 'esg-reports' && (
              <ESGReportView
                dashboardData={dashboardData}
                optimizationData={optimizationData}
                facilityConfig={facilityConfig}
              />
            )}
          </>
        )}
      </main>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        config={facilityConfig}
        onSave={handleSaveSettings}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/60 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-2">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-200">NexusIQ</span>
            <span>• Universal AI-Powered Energy Management Platform</span>
          </div>
          <div>
            <span>Ideathon 2026 | Domain: Sustainable Energy Management | College: NHCE | Team: EcoNexus</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
