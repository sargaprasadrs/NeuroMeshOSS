"use client";

import React, { useEffect, useCallback } from "react";
import Link from "next/link";
import { Play, Loader2, Plus, Cpu, Activity, KeyRound, Workflow } from "lucide-react";
import { useStore } from "@/lib/store";
import { Header } from "@/components/header";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LogConsole } from "@/components/LogConsole";

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
    <div className="min-h-screen">
      <Header />

      {error && (
        <div className="fixed top-16 left-0 right-0 z-40 bg-red-500/10 border-b border-red-500/20 text-red-400 text-sm px-6 py-2.5 backdrop-blur-md">
          {error}
        </div>
      )}

      <main className="pt-24 pb-16">
        <div className="container-custom">
          {/* Hero section */}
          <div className="mb-12">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-white mb-3">
              Command <span className="italic font-light text-neutral-400">Center</span>
            </h1>
            <p className="text-lg text-neutral-500 max-w-2xl">
              Orchestrate autonomous AI agent workflows. Monitor execution, manage secrets, and observe system health.
            </p>
          </div>

          {/* Stat cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
            <Card className="p-5 group hover:border-neutral-700 transition-all duration-300">
              <Link href="/agents" className="block">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-label text-neutral-500">Active Agents</span>
                  <Cpu className="h-4 w-4 text-emerald-500 opacity-60 group-hover:opacity-100 transition-opacity" />
                </div>
                <div className="text-3xl font-bold text-white">{stats.activeAgents}</div>
              </Link>
            </Card>

            <Card className="p-5 group hover:border-neutral-700 transition-all duration-300">
              <Link href="/workflows" className="block">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-label text-neutral-500">Workflows</span>
                  <Workflow className="h-4 w-4 text-blue-500 opacity-60 group-hover:opacity-100 transition-opacity" />
                </div>
                <div className="text-3xl font-bold text-white">{stats.workflows}</div>
              </Link>
            </Card>

            <Card className="p-5 group hover:border-neutral-700 transition-all duration-300">
              <Link href="/metrics" className="block">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-label text-neutral-500">Queue Backlog</span>
                  <Activity className="h-4 w-4 text-purple-500 opacity-60 group-hover:opacity-100 transition-opacity" />
                </div>
                <div className="text-3xl font-bold text-white">{stats.queueBacklog}</div>
              </Link>
            </Card>

            <Card className="p-5 group hover:border-neutral-700 transition-all duration-300">
              <Link href="/secrets" className="block">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-label text-neutral-500">Secrets</span>
                  <KeyRound className="h-4 w-4 text-amber-500 opacity-60 group-hover:opacity-100 transition-opacity" />
                </div>
                <div className="text-3xl font-bold text-white">{stats.secretsCount}</div>
              </Link>
            </Card>
          </div>

          {/* Main content grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Workflows panel */}
            <div className="lg:col-span-4">
              <Card className="p-5 h-full">
                <div className="flex items-center justify-between mb-5">
                  <h3 className="text-sm font-semibold text-white">Workflows</h3>
                  <Link href="/workflows">
                    <Button variant="ghost" size="icon" className="h-7 w-7">
                      <Plus className="h-3.5 w-3.5" />
                    </Button>
                  </Link>
                </div>

                <div className="flex flex-col gap-2">
                  {workflowsLoading ? (
                    <div className="flex items-center justify-center py-8 text-neutral-500">
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      <span className="text-sm">Loading...</span>
                    </div>
                  ) : workflows.length === 0 ? (
                    <p className="text-sm text-neutral-600 text-center py-6">No workflows yet.</p>
                  ) : (
                    workflows.map((wf) => (
                      <div
                        key={wf.id}
                        className="flex items-center justify-between p-3 rounded-lg bg-neutral-800/30 hover:bg-neutral-800/50 border border-neutral-800 hover:border-neutral-700 transition-all duration-200 group"
                      >
                        <div className="flex-1 min-w-0 mr-3">
                          <span className="text-sm font-medium text-neutral-200 truncate block">{wf.name}</span>
                          <span className="text-xs text-neutral-600">{wf.definition?.nodes?.length ?? 0} nodes</span>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={() => handleTriggerRun(wf.id, wf.name)}
                        >
                          <Play className="h-3 w-3" />
                        </Button>
                      </div>
                    ))
                  )}
                </div>
              </Card>
            </div>

            {/* Visual placeholder */}
            <div className="lg:col-span-4">
              <Card className="p-5 h-full flex flex-col items-center justify-center min-h-[300px] relative overflow-hidden">
                <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff03_1px,transparent_1px),linear-gradient(to_bottom,#ffffff03_1px,transparent_1px)] bg-[size:24px_24px]" />
                <div className="relative z-10 text-center">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                    <Workflow className="h-7 w-7 text-emerald-500" />
                  </div>
                  <h4 className="text-sm font-semibold text-neutral-300 mb-1">Visual Editor</h4>
                  <p className="text-xs text-neutral-600 max-w-[200px]">
                    Drag and drop agents, tools, and approvals to build workflows.
                  </p>
                </div>
              </Card>
            </div>

            {/* Log console */}
            <div className="lg:col-span-4">
              <LogConsole logs={logs} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
