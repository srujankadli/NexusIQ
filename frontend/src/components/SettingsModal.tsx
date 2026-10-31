import React, { useState } from 'react';
import { X, Save, Sliders } from 'lucide-react';
import { FacilityConfig } from '../types';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  config: FacilityConfig | null;
  onSave: (updatedConfig: FacilityConfig) => Promise<void>;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  config,
  onSave,
}) => {
  if (!isOpen || !config) return null;

  const [name, setName] = useState(config.name);
  const [contractedDemand, setContractedDemand] = useState(config.grid_contracted_demand_kw);
  const [demandCharge, setDemandCharge] = useState(config.grid_demand_charge_per_kw_month_inr || 280.0);
  const [tariffPeak, setTariffPeak] = useState(config.grid_tariff_peak_inr);
  const [tariffNormal, setTariffNormal] = useState(config.grid_tariff_normal_inr);
  const [tariffOffpeak, setTariffOffpeak] = useState(config.grid_tariff_offpeak_inr);
  const [solarCap, setSolarCap] = useState(config.solar_installed_capacity_kw);
  const [batteryCap, setBatteryCap] = useState(config.battery_capacity_kwh);
  const [saving, setSaving] = useState(false);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!config) return;
    setSaving(true);
    try {
      const updated: FacilityConfig = {
        ...config,
        name,
        level: config.level,
        grid_contracted_demand_kw: Number(contractedDemand),
        grid_demand_charge_per_kw_month_inr: Number(demandCharge),
        grid_tariff_peak_inr: Number(tariffPeak),
        grid_tariff_normal_inr: Number(tariffNormal),
        grid_tariff_offpeak_inr: Number(tariffOffpeak),
        solar_installed_capacity_kw: Number(solarCap),
        has_solar: Number(solarCap) > 0,
        battery_capacity_kwh: Number(batteryCap),
        has_battery: Number(batteryCap) > 0,
      };
      await onSave(updated);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-emerald-400" />
            <h2 className="text-base font-bold text-white">Facility & Tariff Configuration</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="p-5 space-y-4 text-xs">
          <div>
            <label className="block text-slate-400 mb-1 font-medium">Facility / Campus Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Contracted Demand (kW)</label>
              <input
                type="number"
                value={contractedDemand}
                onChange={(e) => setContractedDemand(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Demand Charge (₹ / kW-month)</label>
              <input
                type="number"
                value={demandCharge}
                onChange={(e) => setDemandCharge(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Solar Capacity (kWp)</label>
              <input
                type="number"
                value={solarCap}
                onChange={(e) => setSolarCap(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Battery BESS Size (kWh)</label>
              <input
                type="number"
                value={batteryCap}
                onChange={(e) => setBatteryCap(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Peak Tariff (₹)</label>
              <input
                type="number"
                step="0.1"
                value={tariffPeak}
                onChange={(e) => setTariffPeak(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Normal Tariff (₹)</label>
              <input
                type="number"
                step="0.1"
                value={tariffNormal}
                onChange={(e) => setTariffNormal(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Off-Peak (₹)</label>
              <input
                type="number"
                step="0.1"
                value={tariffOffpeak}
                onChange={(e) => setTariffOffpeak(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          {/* Footer Actions */}
          <div className="pt-4 border-t border-slate-800 flex items-center justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium transition cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center space-x-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-lg shadow-emerald-600/20 transition cursor-pointer"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{saving ? 'Saving...' : 'Save Parameters'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
