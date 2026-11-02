import React, { useState } from 'react';
import {
  Leaf,
  Activity,
  Layers,
  Cpu,
  Sliders,
  UploadCloud,
  FileText,
  Building2,
  CheckCircle2,
  Sparkles,
  Settings,
  Menu,
  X,
  Database
} from 'lucide-react';
import { DeploymentLevel, FacilityConfig, ActiveDatasetStatus } from '../types';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  facilityConfig: FacilityConfig | null;
  activeDataset?: ActiveDatasetStatus | null;
  onSwitchLevel: (level: DeploymentLevel) => void;
  onOpenSettings: () => void;
  onSwitchMode?: (mode: 'demo' | 'uploaded') => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  facilityConfig,
  activeDataset,
  onSwitchLevel,
  onOpenSettings,
  onSwitchMode,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const currentLevel = facilityConfig?.level || 'level_3_campus';

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'digital-twin', label: 'Digital Twin', icon: Building2 },
    { id: 'forecasting', label: 'AI Forecast', icon: Sparkles },
    { id: 'optimization', label: 'Optimization', icon: Cpu },
    { id: 'what-if', label: 'What-If Sim', icon: Sliders },
    { id: 'data-upload', label: 'Data Ingestion', icon: UploadCloud },
    { id: 'esg-reports', label: 'ESG Reports', icon: FileText },
  ];

  function handleTabClick(id: string) {
    setActiveTab(id);
    setMobileMenuOpen(false);
  }

  return (
    <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Identity */}
          <div
            onClick={() => handleTabClick('dashboard')}
            className="flex items-center space-x-3 cursor-pointer group"
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition-transform">
              <Leaf className="w-5 h-5 text-slate-950 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight text-white flex items-center gap-1">
                  Nexus<span className="text-emerald-400">IQ</span>
                </span>
                <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  AI Energy OS
                </span>
              </div>
              <p className="text-[10px] text-slate-400 tracking-wider font-medium">
                Predict. Optimize. Sustain.
              </p>
            </div>
          </div>

          {/* Center Navigation Tabs (Desktop) */}
          <nav className="hidden md:flex items-center space-x-1 bg-slate-950/60 p-1 rounded-xl border border-slate-800/80">
            {navItems.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabClick(tab.id)}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 cursor-pointer ${
                    isActive
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Controls: Active Dataset Indicator, Level Switcher & Settings */}
          <div className="flex items-center space-x-2.5">
            {/* Active Dataset Indicator Badge */}
            <div className="hidden xl:flex items-center space-x-1.5 bg-slate-950/70 px-2.5 py-1 rounded-lg border border-slate-800 text-xs">
              {activeDataset?.source_type === 'uploaded' ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-emerald-300 font-medium truncate max-w-[140px]" title={activeDataset.filename}>
                    {activeDataset.filename}
                  </span>
                  {onSwitchMode && (
                    <button
                      onClick={() => onSwitchMode('demo')}
                      className="ml-1 text-[10px] text-slate-400 hover:text-amber-300 transition underline cursor-pointer"
                      title="Switch back to synthetic benchmark"
                    >
                      Demo
                    </button>
                  )}
                </>
              ) : (
                <>
                  <span className="w-2 h-2 rounded-full bg-blue-400" />
                  <span className="text-blue-300 font-medium">Demo Benchmark</span>
                  <button
                    onClick={() => setActiveTab('data-upload')}
                    className="ml-1 text-[10px] text-slate-400 hover:text-emerald-300 transition underline cursor-pointer"
                    title="Upload CSV to replace demo data"
                  >
                    Upload CSV
                  </button>
                </>
              )}
            </div>

            {/* Deployment Level Selector */}
            <div className="flex items-center bg-slate-800/80 rounded-lg p-0.5 border border-slate-700/60">
              <button
                onClick={() => onSwitchLevel('level_1_basic')}
                title="Level 1: Basic (Only Bills / CSV Data)"
                className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors cursor-pointer ${
                  currentLevel === 'level_1_basic'
                    ? 'bg-blue-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                L1: Basic
              </button>
              <button
                onClick={() => onSwitchLevel('level_2_solar')}
                title="Level 2: Smart Meter & Solar PV"
                className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors cursor-pointer ${
                  currentLevel === 'level_2_solar'
                    ? 'bg-amber-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                L2: Solar
              </button>
              <button
                onClick={() => onSwitchLevel('level_3_campus')}
                title="Level 3: Intelligent Campus (Solar + BESS + Twin)"
                className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors cursor-pointer ${
                  currentLevel === 'level_3_campus'
                    ? 'bg-emerald-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                L3: Microgrid
              </button>
            </div>

            {/* Settings Button */}
            <button
              onClick={onOpenSettings}
              title="Configure Facility Parameters & Tariffs"
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 transition cursor-pointer"
            >
              <Settings className="w-4 h-4" />
            </button>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 transition cursor-pointer"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-slate-900 border-b border-slate-800 px-4 pt-2 pb-4 space-y-1 shadow-2xl">
          {navItems.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => handleTabClick(tab.id)}
                className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition cursor-pointer ${
                  isActive
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800'
                }`}
              >
                <Icon className="w-4 h-4 text-emerald-400" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
};
