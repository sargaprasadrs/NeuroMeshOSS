import { create } from "zustand";

interface Workflow {
  id: string;
  name: string;
  definition: any;
}

interface RunState {
  workflows: Workflow[];
  activeRunId: string | null;
  logs: string[];
  setWorkflows: (workflows: Workflow[]) => void;
  setActiveRunId: (runId: string | null) => void;
  addLog: (log: string) => void;
  clearLogs: () => void;
}

export const useStore = create<RunState>((set) => ({
  workflows: [],
  activeRunId: null,
  logs: [],
  setWorkflows: (workflows) => set({ workflows }),
  setActiveRunId: (runId) => set({ activeRunId: runId }),
  addLog: (log) => set((state) => ({ logs: [...state.logs, log] })),
  clearLogs: () => set({ logs: [] }),
}));
