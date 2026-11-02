import {
  DeploymentLevel,
  FacilityConfig,
  LiveDashboardResponse,
  ForecastResponse,
  OptimizationResponse,
  WhatIfRequest,
  WhatIfResponse,
  CSVUploadSummary,
  BuildingLoad,
  ActiveDatasetStatus
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

export const api = {
  async getHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      return await res.json();
    } catch {
      return { status: 'offline', version: '1.0.0' };
    }
  },

  async getDatasetStatus(): Promise<ActiveDatasetStatus> {
    const res = await fetch(`${API_BASE}/dataset/status`);
    if (!res.ok) throw new Error('Failed to fetch dataset status');
    return res.json();
  },

  async switchDatasetMode(mode: 'demo' | 'uploaded', level?: DeploymentLevel): Promise<ActiveDatasetStatus> {
    const res = await fetch(`${API_BASE}/dataset/switch-mode`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode, level }),
    });
    if (!res.ok) throw new Error('Failed to switch dataset mode');
    return res.json();
  },

  async getProfile(): Promise<FacilityConfig> {
    const res = await fetch(`${API_BASE}/profile`);
    if (!res.ok) throw new Error('Failed to fetch profile');
    return res.json();
  },

  async switchLevel(level: DeploymentLevel): Promise<FacilityConfig> {
    const res = await fetch(`${API_BASE}/profile/switch?level=${level}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to switch level');
    return res.json();
  },

  async updateSettings(config: FacilityConfig): Promise<FacilityConfig> {
    const res = await fetch(`${API_BASE}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error('Failed to update settings');
    return res.json();
  },

  async getLiveDashboard(): Promise<LiveDashboardResponse> {
    const res = await fetch(`${API_BASE}/dashboard/live`);
    if (!res.ok) throw new Error('Failed to fetch dashboard');
    return res.json();
  },

  async getForecast(cloudCover: number = 15): Promise<ForecastResponse> {
    const res = await fetch(`${API_BASE}/forecast/24h?cloud_cover=${cloudCover}`);
    if (!res.ok) throw new Error('Failed to fetch forecast');
    return res.json();
  },

  async remediateAnomaly(anomalyId: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/anomaly/remediate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ anomaly_id: anomalyId }),
    });
    if (!res.ok) throw new Error('Failed to remediate anomaly');
    return res.json();
  },

  async runOptimization(flexibleShiftEnabled: boolean = true): Promise<OptimizationResponse> {
    const res = await fetch(`${API_BASE}/optimize?flexible_shift_enabled=${flexibleShiftEnabled}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to run optimization');
    return res.json();
  },

  getScheduleCsvUrl(): string {
    return `${API_BASE}/optimization/download-schedule-csv`;
  },

  async runWhatIf(request: WhatIfRequest): Promise<WhatIfResponse> {
    const res = await fetch(`${API_BASE}/what-if`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!res.ok) throw new Error('Failed to run what-if simulation');
    return res.json();
  },

  async uploadCSV(file: File): Promise<CSVUploadSummary> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/upload-csv`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async loadSampleDataset(): Promise<CSVUploadSummary> {
    const res = await fetch(`${API_BASE}/load-sample`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to load sample dataset');
    return res.json();
  },

  async getBuildings(): Promise<BuildingLoad[]> {
    const res = await fetch(`${API_BASE}/campus/buildings`);
    if (!res.ok) throw new Error('Failed to fetch campus buildings');
    return res.json();
  },

  async toggleBuildingShift(bldId: string) {
    const res = await fetch(`${API_BASE}/buildings/${bldId}/toggle-shift`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to toggle building shift');
    return res.json();
  },

  getSampleCSVUrl(): string {
    return `${API_BASE}/download-sample-csv`;
  }
};
