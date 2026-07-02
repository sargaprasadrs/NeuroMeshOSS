"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Play, ShieldAlert, Cpu, Layers, Activity, Plus, Sparkles, KeyRound } from "lucide-react";

export default function Dashboard() {
  const [logs, setLogs] = useState<string[]>([
    "[system] Engine initialized. Awaiting workflow triggers.",
    "[redis] Stream consumer connected to topic: workflow_jobs",
  ]);

  const [workflows] = useState([
    { id: "wf-1", name: "Market Analyzer Agent Flow", status: "active" },
    { id: "wf-2", name: "Customer Support Triager", status: "paused" },
    { id: "wf-3", name: "Automated Code Review Agent", status: "active" },
  ]);

  const triggerMockRun = () => {
    setLogs((prev) => [
      ...prev,
      `[trigger] Manual run request initiated for Market Analyzer Agent Flow`,
      `[engine] Created run execution context ID: run_${Math.floor(Math.random() * 100000)}`,
      `[queue] Pushed execution token to Redis Stream.`,
    ]);
  };

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

      {/* Grid Stats Header */}
      <main className="flex-1 p-6 flex flex-col gap-6 max-w-7xl mx-auto w-full">
        <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Link href="/agents" className="bg-zinc-900/60 border border-zinc-800 p-4 rounded-xl flex items-center justify-between hover:border-zinc-700 transition">
            <div>
              <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Active Agents</p>
              <h3 className="text-2xl font-bold mt-1 text-zinc-200">12</h3>
            </div>
            <Cpu className="h-8 w-8 text-emerald-500 opacity-80" />
          </Link>

          <Link href="/workflows" className="bg-zinc-900/60 border border-zinc-800 p-4 rounded-xl flex items-center justify-between hover:border-zinc-700 transition">
            <div>
              <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Running Flows</p>
              <h3 className="text-2xl font-bold mt-1 text-zinc-200">3</h3>
            </div>
            <Activity className="h-8 w-8 text-blue-500 opacity-80" />
          </Link>

          <Link href="/metrics" className="bg-zinc-900/60 border border-zinc-800 p-4 rounded-xl flex items-center justify-between hover:border-zinc-700 transition">
            <div>
              <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Queue Latency</p>
              <h3 className="text-2xl font-bold mt-1 text-zinc-200">2ms</h3>
            </div>
            <Activity className="h-8 w-8 text-purple-500 opacity-80" />
          </Link>

          <Link href="/secrets" className="bg-zinc-900/60 border border-zinc-800 p-4 rounded-xl flex items-center justify-between hover:border-zinc-700 transition">
            <div>
              <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Secrets Vault</p>
              <h3 className="text-2xl font-bold mt-1 text-zinc-200">4</h3>
            </div>
            <ShieldAlert className="h-8 w-8 text-amber-500 opacity-80" />
          </Link>
        </section>

        {/* Dashboard Workspaces Split */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[500px]">
          {/* Left panel: Workflows list */}
          <aside className="lg:col-span-3 bg-zinc-900/40 border border-zinc-800 rounded-xl p-4 flex flex-col gap-4">
            <div className="flex justify-between items-center">
              <h4 className="font-semibold text-zinc-200">Workflows</h4>
              <button className="p-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-white transition">
                <Plus className="h-4 w-4" />
              </button>
            </div>
            <div className="flex flex-col gap-2">
              {workflows.map((wf) => (
                <div
                  key={wf.id}
                  className="p-3 bg-zinc-900/80 hover:bg-zinc-800/80 border border-zinc-800 hover:border-zinc-700 rounded-lg cursor-pointer transition flex items-center justify-between group"
                >
                  <span className="text-sm font-medium text-zinc-300">{wf.name}</span>
                  <button
                    onClick={triggerMockRun}
                    className="p-1 bg-zinc-800 hover:bg-emerald-600 rounded text-zinc-400 group-hover:text-white transition"
                  >
                    <Play className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          </aside>

          {/* Center visual editor placeholder */}
          <section className="lg:col-span-6 bg-zinc-900/30 border border-zinc-800 rounded-xl flex flex-col items-center justify-center p-6 relative overflow-hidden">
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f293710_1px,transparent_1px),linear-gradient(to_bottom,#1f293710_1px,transparent_1px)] bg-[size:24px_24px]"></div>
            <div className="z-10 text-center flex flex-col items-center gap-2">
              <Layers className="h-12 w-12 text-zinc-600 mb-2" />
              <h5 className="font-semibold text-zinc-300">Visual Workflow Editor</h5>
              <p className="text-sm text-zinc-500 max-w-sm">
                Connect agents, vector storage databases, and human approval steps to orchestrate complex execution loops.
              </p>
            </div>
          </section>

          {/* Right trace log console */}
          <section className="lg:col-span-3 bg-zinc-950 border border-zinc-800 rounded-xl p-4 flex flex-col gap-3 font-mono text-xs">
            <h4 className="font-semibold font-sans text-zinc-300">Real-Time Trace Stream</h4>
            <div className="flex-1 bg-black/60 rounded-lg p-3 overflow-y-auto max-h-[400px] flex flex-col gap-2 text-emerald-400 border border-zinc-900">
              {logs.map((log, index) => (
                <div key={index} className="leading-relaxed">
                  {log}
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
