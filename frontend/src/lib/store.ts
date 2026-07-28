import { create } from "zustand";
import { apiClient, setAuthToken } from "./api-client";

// ── Types ────────────────────────────────────────────────────────────────

export interface Workflow {
  id: string;
  name: string;
  definition: { nodes: any[]; edges: any[] };
  version: number;
}

export interface WorkflowRun {
  run_id: string;
  workflow_id: string;
  status: string;
  version: number;
}

export interface DashboardStats {
  workflows: number;
  activeAgents: number;
  queueBacklog: number;
  secretsCount: number;
}

// ── Store ────────────────────────────────────────────────────────────────

interface AppState {
  // Auth
  token: string | null;
  setToken: (token: string | null) => void;

  // Workflows
  workflows: Workflow[];
  workflowsLoading: boolean;
  fetchWorkflows: () => Promise<void>;

  // Runs
  runs: WorkflowRun[];
  runsLoading: boolean;
  triggerRun: (workflowId: string) => Promise<WorkflowRun | null>;

  // Logs
  logs: string[];
  addLog: (log: string) => void;
  clearLogs: () => void;

  // Dashboard stats (derived from fetched data)
  stats: DashboardStats;

  // Error state
  error: string | null;
  setError: (error: string | null) => void;
}

export const useStore = create<AppState>((set, get) => ({
  // ── Auth ──────────────────────────────────────────────────────────
  token: null,
  setToken: (token) => {
    setAuthToken(token);
    set({ token });
  },

  // ── Workflows ─────────────────────────────────────────────────────
  workflows: [],
  workflowsLoading: false,
  fetchWorkflows: async () => {
    set({ workflowsLoading: true, error: null });
    try {
      const { data } = await apiClient.get("/workflows/");
      const workflows: Workflow[] = data.items || [];
      set({
        workflows,
        workflowsLoading: false,
        stats: { ...get().stats, workflows: workflows.length },
      });
    } catch (err: any) {
      const message = err.response?.data?.detail || "Failed to fetch workflows";
      set({ workflowsLoading: false, error: message });
      console.error("fetchWorkflows error:", err);
    }
  },

  // ── Runs ──────────────────────────────────────────────────────────
  runs: [],
  runsLoading: false,
  triggerRun: async (workflowId) => {
    set({ error: null });
    try {
      const { data } = await apiClient.post(`/workflows/${workflowId}/run`);
      const run: WorkflowRun = {
        run_id: data.run_id,
        workflow_id: data.workflow_id,
        status: data.status,
        version: data.version,
      };
      set((state) => ({ runs: [run, ...state.runs] }));
      get().addLog(`[queue] Run ${run.run_id} triggered for workflow ${workflowId}`);
      return run;
    } catch (err: any) {
      const message = err.response?.data?.detail || "Failed to trigger run";
      set({ error: message });
      get().addLog(`[error] Failed to trigger run: ${message}`);
      console.error("triggerRun error:", err);
      return null;
    }
  },

  // ── Logs ──────────────────────────────────────────────────────────
  logs: [
    "[system] Engine initialized. Awaiting workflow triggers.",
    "[redis] Stream consumer connected to topic: workflow_jobs",
  ],
  addLog: (log) =>
    set((state) => ({
      logs: [...state.logs.slice(-200), `[${new Date().toLocaleTimeString()}] ${log}`],
    })),
  clearLogs: () => set({ logs: [] }),

  // ── Stats ─────────────────────────────────────────────────────────
  stats: {
    workflows: 0,
    activeAgents: 0,
    queueBacklog: 0,
    secretsCount: 0,
  },

  // ── Error ─────────────────────────────────────────────────────────
  error: null,
  setError: (error) => set({ error }),
}));
