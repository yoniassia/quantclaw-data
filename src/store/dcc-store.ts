import { create } from 'zustand';

export type DCCView = 'mission-control' | 'module-explorer' | 'pipeline' | 'quality' | 'alerts' | 'sources' | 'config';

export interface TierDistribution {
  bronze: number;
  silver: number;
  gold: number;
  platinum: number;
  none: number;
}

export interface DCCStats {
  modules: { total: number; active: number; tiers: TierDistribution };
  cadence: { cadence: string; count: number }[];
  alerts: { unresolved: number; critical: number; warning: number; info: number };
  pipeline: {
    totalRuns: number; success: number; failed: number; running: number;
    todayRuns: number; todaySuccess: number; avgDurationMs: number;
  };
  freshness: { onSchedule: number; overdue: number };
}

export interface Module {
  id: number;
  name: string;
  display_name: string | null;
  cadence: string;
  granularity: string;
  current_tier: string;
  quality_score: number;
  is_active: boolean;
  last_run_at: string | null;
  last_success_at: string | null;
  next_run_at: string | null;
  run_count: number;
  error_count: number;
  consecutive_failures: number;
  avg_duration_ms: number | null;
  source_url: string | null;
}

export interface PipelineRun {
  id: number;
  module_id: number;
  module_name: string;
  tier_target: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  duration_ms: number | null;
  rows_in: number;
  rows_out: number;
  rows_failed: number;
  retry_attempt: number;
  error_message: string | null;
}

export interface Alert {
  id: number;
  module_id: number | null;
  module_name: string | null;
  run_id: number | null;
  severity: 'info' | 'warning' | 'critical';
  category: string | null;
  message: string;
  details: Record<string, unknown>;
  resolved: boolean;
  resolved_by: string | null;
  resolved_at: string | null;
  created_at: string;
}

export interface ModuleDetail {
  module: Module & { source_file: string | null; output_schema: unknown; created_at: string; updated_at: string };
  runs: PipelineRun[];
  qualityChecks: { id: number; check_type: string; passed: boolean; score: number; details: Record<string, unknown>; checked_at: string }[];
  tags: { category: string; label: string }[];
}

export interface ThroughputData {
  hourly: { hour: string; total: number; success: number; failed: number }[];
  daily: { day: string; total: number; success: number; failed: number; avgMs: number }[];
}

interface DCCStore {
  view: DCCView;
  stats: DCCStats | null;
  modules: Module[];
  modulesTotal: number;
  recentRuns: PipelineRun[];
  alerts: Alert[];
  loading: boolean;
  error: string | null;
  selectedModuleId: number | null;
  moduleDetail: ModuleDetail | null;
  throughput: ThroughputData | null;

  setView: (view: DCCView) => void;
  setSelectedModule: (id: number | null) => void;
  fetchStats: () => Promise<void>;
  fetchModules: (params?: Record<string, string>) => Promise<void>;
  fetchRecentRuns: () => Promise<void>;
  fetchAlerts: () => Promise<void>;
  resolveAlert: (id: number) => Promise<void>;
  fetchModuleDetail: (id: number) => Promise<void>;
  fetchThroughput: () => Promise<void>;
}

export const useDCCStore = create<DCCStore>((set, get) => ({
  view: 'mission-control',
  stats: null,
  modules: [],
  modulesTotal: 0,
  recentRuns: [],
  alerts: [],
  loading: false,
  error: null,
  selectedModuleId: null,
  moduleDetail: null,
  throughput: null,

  setView: (view) => set({ view }),
  setSelectedModule: (id) => set({ selectedModuleId: id, moduleDetail: null }),

  fetchStats: async () => {
    try {
      set({ loading: true, error: null });
      const res = await fetch('/api/dcc/stats');
      if (!res.ok) throw new Error('Failed to fetch stats');
      const data = await res.json();
      set({ stats: data, loading: false });
    } catch (err) {
      set({ error: (err as Error).message, loading: false });
    }
  },

  fetchModules: async (params = {}) => {
    try {
      const qs = new URLSearchParams(params).toString();
      const res = await fetch(`/api/dcc/modules?${qs}`);
      if (!res.ok) throw new Error('Failed to fetch modules');
      const data = await res.json();
      set({ modules: data.modules, modulesTotal: data.total });
    } catch (err) {
      set({ error: (err as Error).message });
    }
  },

  fetchRecentRuns: async () => {
    try {
      const res = await fetch('/api/dcc/pipeline/recent?limit=30');
      if (!res.ok) throw new Error('Failed to fetch runs');
      const data = await res.json();
      set({ recentRuns: data.runs });
    } catch (err) {
      set({ error: (err as Error).message });
    }
  },

  fetchAlerts: async () => {
    try {
      const res = await fetch('/api/dcc/alerts?resolved=false');
      if (!res.ok) throw new Error('Failed to fetch alerts');
      const data = await res.json();
      set({ alerts: data.alerts });
    } catch (err) {
      set({ error: (err as Error).message });
    }
  },

  resolveAlert: async (id) => {
    try {
      const res = await fetch('/api/dcc/alerts', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, action: 'resolve' }),
      });
      if (!res.ok) throw new Error('Failed to resolve alert');
      const alerts = get().alerts.filter(a => a.id !== id);
      set({ alerts });
    } catch (err) {
      set({ error: (err as Error).message });
    }
  },

  fetchModuleDetail: async (id) => {
    try {
      const res = await fetch(`/api/dcc/modules/${id}`);
      if (!res.ok) throw new Error('Failed to fetch module detail');
      const data = await res.json();
      set({ moduleDetail: data });
    } catch (err) {
      set({ error: (err as Error).message });
    }
  },

  fetchThroughput: async () => {
    try {
      const res = await fetch('/api/dcc/pipeline/throughput');
      if (!res.ok) throw new Error('Failed to fetch throughput');
      const data = await res.json();
      set({ throughput: data });
    } catch (err) {
      set({ error: (err as Error).message });
    }
  },
}));
