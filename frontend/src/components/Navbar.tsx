import React from 'react';
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
  Settings
} from 'lucide-react';
import { DeploymentLevel, FacilityConfig } from '../types';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  facilityConfig: FacilityConfig | null;
  onSwitchLevel: (level: DeploymentLevel) => void;
  onOpenSettings: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  facilityConfig,
  onSwitchLevel,
  onOpenSettings,
}) => {
  const currentLevel = facilityConfig?.level || 'level_3_campus';

  return (
    <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Identity */}
          <div
            onClick={() => setActiveTab('dashboard')}
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

          {/* Center Navigation Tabs */}
          <nav className="hidden md:flex items-center space-x-1 bg-slate-950/60 p-1 rounded-xl border border-slate-800/80">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: Activity },
              { id: 'digital-twin', label: 'Digital Twin', icon: Building2 },
              { id: 'forecasting', label: 'AI Forecast', icon: Sparkles },
              { id: 'optimization', label: 'Optimization', icon: Cpu },
              { id: 'what-if', label: 'What-If Sim', icon: Sliders },
              { id: 'data-upload', label: 'Data Ingestion', icon: UploadCloud },
              { id: 'esg-reports', label: 'ESG Reports', icon: FileText },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
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

          {/* Right Controls: Level Switcher & Settings */}
          <div className="flex items-center space-x-2.5">
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

            {/* Institution Badge */}
            <div className="hidden lg:flex flex-col text-right pl-2 border-l border-slate-800">
              <span className="text-[11px] font-semibold text-slate-300">
                NHCE | EcoNexus
              </span>
              <span className="text-[10px] text-emerald-400 flex items-center justify-end gap-1">
                <CheckCircle2 className="w-2.5 h-2.5" />
                Ideathon 2026
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
