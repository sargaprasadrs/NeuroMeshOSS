"use client";

import React, { useEffect, useCallback } from "react";
import Link from "next/link";
import { Play, ShieldAlert, Cpu, Layers, Activity, Plus, Loader2 } from "lucide-react";
import { LogConsole } from "@/components/LogConsole";
import { SpotlightCard } from "@/components/SpotlightCard";
import SwarmIntelligence from "@/components/SwarmIntelligence";
import { useStore } from "@/lib/store";

export default function Dashboard() {
  const {
    workflows,
    workflowsLoading,
    fetchWorkflows,
    triggerRun,
    logs,
    stats,
    error,
  } = useStore();

  // Fetch workflows on mount
  useEffect(() => {
    fetchWorkflows();
  }, [fetchWorkflows]);

  const handleTriggerRun = useCallback(
    async (workflowId: string, workflowName: string) => {
      const run = await triggerRun(workflowId);
      if (run) {
        useStore.getState().addLog(`[engine] Run ${run.run_id} created for "${workflowName}"`);
      }
    },
    [triggerRun]
  );

  return (
    <div className="flex flex-col min-h-screen">
      {/* Top Navbar */}
      <header className="flex items-center justify-between border-b border-zinc-800 bg-zinc-900/50 backdrop-blur px-6 py-4">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Layers className="h-6 w-6 text-emerald-500" />
            <span className="font-bold text-lg tracking-wider text-zinc-100">NeuroMeshOSS</span>
          </div>
          <nav className="hidden md:flex items-center gap-4 text-sm text-zinc-400 font-medium">
            <Link href="/workflows" className="hover:text-zinc-200 transition">Workflows</Link>
            <Link href="/agents" className="hover:text-zinc-200 transition">Agents</Link>
            <Link href="/plugins" className="hover:text-zinc-200 transition">Plugins</Link>
            <Link href="/secrets" className="hover:text-zinc-200 transition">Secrets</Link>
            <Link href="/metrics" className="hover:text-zinc-200 transition">Metrics</Link>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-ping"></span>
          <span className="text-sm font-medium text-zinc-400">Local Engine Connected</span>
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm px-6 py-2">
          {error}
        </div>
      )}

      {/* Grid Stats Header */}
      <main className="flex-1 p-6 flex flex-col gap-6 max-w-7xl mx-auto w-full">
        <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <SpotlightCard className="p-0 border border-zinc-800 hover:border-zinc-700 bg-zinc-900/60 rounded-xl" glowColor="rgba(16, 185, 129, 0.06)">
            <Link href="/agents" className="flex items-center justify-between p-4 w-full h-full focus:outline-none" aria-label="View Active Agents Registry">
              <div>
                <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Active Agents</p>
                <h3 className="text-2xl font-bold mt-1 text-zinc-200">{stats.activeAgents}</h3>
              </div>
              <Cpu className="h-8 w-8 text-emerald-500 opacity-80" />
            </Link>
          </SpotlightCard>

          <SpotlightCard className="p-0 border border-zinc-800 hover:border-zinc-700 bg-zinc-900/60 rounded-xl" glowColor="rgba(59, 130, 246, 0.06)">
            <Link href="/workflows" className="flex items-center justify-between p-4 w-full h-full focus:outline-none" aria-label="View Active Workflows List">
              <div>
                <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Workflows</p>
                <h3 className="text-2xl font-bold mt-1 text-zinc-200">{stats.workflows}</h3>
              </div>
              <Activity className="h-8 w-8 text-blue-500 opacity-80" />
            </Link>
          </SpotlightCard>

          <SpotlightCard className="p-0 border border-zinc-800 hover:border-zinc-700 bg-zinc-900/60 rounded-xl" glowColor="rgba(168, 85, 247, 0.06)">
            <Link href="/metrics" className="flex items-center justify-between p-4 w-full h-full focus:outline-none" aria-label="View Queue Telemetry Metrics">
              <div>
                <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Queue Backlog</p>
                <h3 className="text-2xl font-bold mt-1 text-zinc-200">{stats.queueBacklog}</h3>
              </div>
              <Activity className="h-8 w-8 text-purple-500 opacity-80" />
            </Link>
          </SpotlightCard>

          <SpotlightCard className="p-0 border border-zinc-800 hover:border-zinc-700 bg-zinc-900/60 rounded-xl" glowColor="rgba(245, 158, 11, 0.06)">
            <Link href="/secrets" className="flex items-center justify-between p-4 w-full h-full focus:outline-none" aria-label="View Encrypted Secrets Vault">
              <div>
                <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Secrets Vault</p>
                <h3 className="text-2xl font-bold mt-1 text-zinc-200">{stats.secretsCount}</h3>
              </div>
              <ShieldAlert className="h-8 w-8 text-amber-500 opacity-80" />
            </Link>
          </SpotlightCard>
        </section>

        {/* Dashboard Workspaces Split */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[500px]">
          {/* Left panel: Workflows list */}
          <aside className="lg:col-span-3 bg-zinc-900/40 border border-zinc-800 rounded-xl p-4 flex flex-col gap-4">
            <div className="flex justify-between items-center">
              <h4 className="font-semibold text-zinc-200">Workflows</h4>
              <Link
                href="/workflows"
                className="p-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-white transition"
              >
                <Plus className="h-4 w-4" />
              </Link>
            </div>
            <div className="flex flex-col gap-2">
              {workflowsLoading ? (
                <div className="flex items-center justify-center py-8 text-zinc-500">
                  <Loader2 className="h-5 w-5 animate-spin mr-2" />
                  Loading workflows...
                </div>
              ) : workflows.length === 0 ? (
                <p className="text-xs text-zinc-500 text-center py-4">No workflows found. Create one to get started.</p>
              ) : (
                workflows.map((wf) => (
                  <div
                    key={wf.id}
                    className="p-3 bg-zinc-900/80 hover:bg-zinc-800/80 border border-zinc-800 hover:border-zinc-700 rounded-lg cursor-pointer transition flex items-center justify-between group"
                  >
                    <span className="text-sm font-medium text-zinc-300 truncate mr-2">{wf.name}</span>
                    <button
                      onClick={() => handleTriggerRun(wf.id, wf.name)}
                      aria-label={`Trigger manual run for workflow ${wf.name}`}
                      className="p-1 bg-zinc-800 hover:bg-emerald-600 rounded text-zinc-400 group-hover:text-white transition focus:outline-none focus:ring-1 focus:ring-emerald-500 shrink-0"
                    >
                      <Play className="h-3 w-3" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </aside>

          {/* Center visual editor placeholder */}
          <section className="lg:col-span-6 bg-zinc-900/30 border border-zinc-800 rounded-xl flex flex-col items-center justify-center p-6 relative overflow-hidden">
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f293710_1px,transparent_1px),linear-gradient(to_bottom,#1f293710_1px,transparent_1px)] bg-[size:24px_24px]"></div>
            <div className="z-10 text-center flex flex-col items-center gap-4 w-full">
              <div className="flex flex-col items-center gap-1">
                <h5 className="font-semibold text-zinc-300">Visual Workflow Editor</h5>
                <p className="text-xs text-zinc-500 max-w-sm">
                  Connect agents, vector databases, and human approvals.
                </p>
              </div>
              <SwarmIntelligence />
            </div>
          </section>

          {/* Right trace log console */}
          <LogConsole logs={logs} />
        </div>
      </main>
    </div>
  );
}
