"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Activity, ArrowLeft, BarChart2, CheckCircle2, ShieldAlert } from "lucide-react";

export default function MetricsPage() {
  const [telemetry] = useState({
    cpu: "12%",
    ram: "1.4 GB / 8.0 GB",
    activeDbConnections: "2",
    avgLatency: "2.4ms",
    otelStatus: "CONNECTED",
  });

  return (
    <div className="flex flex-col min-h-screen bg-zinc-950 text-zinc-50">
      <header className="flex items-center justify-between border-b border-zinc-800 bg-zinc-900/50 backdrop-blur px-6 py-4">
        <div className="flex items-center gap-4">
          <Link href="/" className="p-1 bg-zinc-800 hover:bg-zinc-700 rounded transition text-zinc-300">
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div className="flex items-center gap-2">
            <BarChart2 className="h-6 w-6 text-emerald-500" />
            <span className="font-bold text-lg text-zinc-100">Telemetry & Performance</span>
          </div>
        </div>
      </header>

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full flex flex-col gap-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-zinc-900/40 border border-zinc-800 p-4 rounded-xl">
            <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Active DB Sessions</p>
            <h3 className="text-2xl font-bold mt-1 text-zinc-200">{telemetry.activeDbConnections}</h3>
          </div>
          <div className="bg-zinc-900/40 border border-zinc-800 p-4 rounded-xl">
            <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Average API Latency</p>
            <h3 className="text-2xl font-bold mt-1 text-zinc-200">{telemetry.avgLatency}</h3>
          </div>
          <div className="bg-zinc-900/40 border border-zinc-800 p-4 rounded-xl">
            <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">CPU Utilisation</p>
            <h3 className="text-2xl font-bold mt-1 text-zinc-200">{telemetry.cpu}</h3>
          </div>
          <div className="bg-zinc-900/40 border border-zinc-800 p-4 rounded-xl">
            <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">RAM Allocation</p>
            <h3 className="text-2xl font-bold mt-1 text-zinc-200">{telemetry.ram}</h3>
          </div>
        </div>

        <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-6 flex flex-col gap-4">
          <h3 className="font-semibold text-lg text-zinc-200 flex items-center gap-2">
            <Activity className="h-5 w-5 text-emerald-500" /> OpenTelemetry Connection Status
          </h3>
          <div className="flex items-center gap-3">
            <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-ping"></span>
            <span className="text-sm font-semibold text-zinc-300">OTel Exporter: Active</span>
          </div>
          <p className="text-sm text-zinc-400 max-w-2xl leading-relaxed">
            Spans and traces are exported over HTTP/gRPC formats to the collector endpoint configured at <code className="bg-zinc-800 px-1.5 py-0.5 rounded font-mono text-zinc-300">http://localhost:4317</code>.
          </p>
        </div>
      </main>
    </div>
  );
}
