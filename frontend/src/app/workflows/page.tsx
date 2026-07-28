"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { Layers, ArrowLeft, Play, CheckCircle2, Clock, XCircle, Loader2 } from "lucide-react";
import { useStore } from "@/lib/store";

export default function WorkflowsPage() {
  const {
    workflows,
    workflowsLoading,
    fetchWorkflows,
    runs,
    triggerRun,
    error,
  } = useStore();

  useEffect(() => {
    fetchWorkflows();
  }, [fetchWorkflows]);

  return (
    <div className="flex flex-col min-h-screen bg-zinc-950 text-zinc-50">
      <header className="flex items-center justify-between border-b border-zinc-800 bg-zinc-900/50 backdrop-blur px-6 py-4">
        <div className="flex items-center gap-4">
          <Link href="/" className="p-1 bg-zinc-800 hover:bg-zinc-700 rounded transition text-zinc-300">
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div className="flex items-center gap-2">
            <Layers className="h-6 w-6 text-emerald-500" />
            <span className="font-bold text-lg text-zinc-100">Workflows & Run History</span>
          </div>
        </div>
      </header>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm px-6 py-2">
          {error}
        </div>
      )}

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full flex flex-col gap-6">
        {/* Workflow Definitions */}
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-6 flex flex-col gap-4">
          <h3 className="font-semibold text-lg text-zinc-200">Registered Workflows</h3>
          {workflowsLoading ? (
            <div className="flex items-center justify-center py-8 text-zinc-500">
              <Loader2 className="h-5 w-5 animate-spin mr-2" />
              Loading workflows...
            </div>
          ) : workflows.length === 0 ? (
            <p className="text-sm text-zinc-500 text-center py-6">No workflows found. Create one via the API or CLI.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-zinc-800 text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                    <th className="py-3 px-4">Workflow ID</th>
                    <th className="py-3 px-4">Name</th>
                    <th className="py-3 px-4">Nodes</th>
                    <th className="py-3 px-4">Version</th>
                    <th className="py-3 px-4">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-900 text-sm">
                  {workflows.map((wf) => (
                    <tr key={wf.id} className="hover:bg-zinc-900/30 transition">
                      <td className="py-3 px-4 font-mono text-emerald-400 text-xs">{wf.id.slice(0, 8)}...</td>
                      <td className="py-3 px-4 font-medium text-zinc-300">{wf.name}</td>
                      <td className="py-3 px-4 text-zinc-400">{wf.definition?.nodes?.length ?? 0}</td>
                      <td className="py-3 px-4 text-zinc-400">v{wf.version}</td>
                      <td className="py-3 px-4">
                        <button
                          onClick={() => triggerRun(wf.id)}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-xs font-semibold text-white transition"
                        >
                          <Play className="h-3 w-3" /> Run
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Run History */}
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-6 flex flex-col gap-4">
          <h3 className="font-semibold text-lg text-zinc-200">Execution Runs</h3>
          {runs.length === 0 ? (
            <p className="text-sm text-zinc-500 text-center py-6">No runs yet. Trigger a workflow to see execution history.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-zinc-800 text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                    <th className="py-3 px-4">Run ID</th>
                    <th className="py-3 px-4">Workflow ID</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Version</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-900 text-sm">
                  {runs.map((run) => (
                    <tr key={run.run_id} className="hover:bg-zinc-900/30 transition">
                      <td className="py-3 px-4 font-mono text-emerald-400 text-xs">{run.run_id.slice(0, 8)}...</td>
                      <td className="py-3 px-4 font-mono text-zinc-400 text-xs">{run.workflow_id.slice(0, 8)}...</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-semibold ${
                          run.status === "SUCCESS" ? "bg-emerald-500/10 text-emerald-500" :
                          run.status === "RUNNING" || run.status === "PENDING" ? "bg-blue-500/10 text-blue-400" :
                          run.status === "PAUSED" ? "bg-amber-500/10 text-amber-400" :
                          "bg-red-500/10 text-red-500"
                        }`}>
                          {run.status === "SUCCESS" && <CheckCircle2 className="h-3 w-3" />}
                          {(run.status === "RUNNING" || run.status === "PENDING") && <Clock className="h-3 w-3 animate-spin" />}
                          {run.status === "FAILED" && <XCircle className="h-3 w-3" />}
                          {run.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-zinc-400">v{run.version}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
