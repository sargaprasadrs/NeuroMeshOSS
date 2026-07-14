"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Activity, ArrowLeft, BarChart2 } from "lucide-react";
import { SpotlightCard } from "@/components/SpotlightCard";

export default function MetricsPage() {
  const [telemetry] = useState({
    cpu: "12%",
    ram: "1.4 GB / 8.0 GB",
    activeDbConnections: "2",
    avgLatency: "2.4ms",
    otelStatus: "CONNECTED",
  });

  return (
    <div className="flex flex-col min-h-screen bg-black text-zinc-50 font-sans">
      <header className="flex items-center justify-between border-b border-zinc-900 bg-black px-6 py-4 relative z-50">
        <div className="flex items-center gap-4">
          <Link href="/" className="p-1.5 hover:bg-zinc-900 border border-zinc-900 rounded transition text-zinc-400 hover:text-zinc-200 flex items-center justify-center">
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div className="flex items-center gap-2.5">
            <div className="h-5 w-5 rounded bg-emerald-500 flex items-center justify-center">
              <BarChart2 className="h-3 w-3 text-black stroke-[2.5]" />
            </div>
            <span className="font-semibold text-sm tracking-tight text-zinc-100">
              Metrics
            </span>
          </div>
        </div>
      </header>

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full flex flex-col gap-6">
        <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <SpotlightCard>
            <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Active DB Sessions</p>
            <h3 className="text-2xl font-semibold mt-1.5 text-zinc-100 tracking-tight">{telemetry.activeDbConnections}</h3>
          </SpotlightCard>

          <SpotlightCard>
            <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Average API Latency</p>
            <h3 className="text-2xl font-semibold mt-1.5 text-zinc-100 tracking-tight">{telemetry.avgLatency}</h3>
          </SpotlightCard>

          <SpotlightCard>
            <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">CPU Utilisation</p>
            <h3 className="text-2xl font-semibold mt-1.5 text-zinc-100 tracking-tight">{telemetry.cpu}</h3>
          </SpotlightCard>

          <SpotlightCard>
            <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">RAM Allocation</p>
            <h3 className="text-2xl font-semibold mt-1.5 text-zinc-100 tracking-tight truncate" title={telemetry.ram}>
              {telemetry.ram.split("/")[0].trim()}
              <span className="text-xs text-zinc-500 font-normal"> / {telemetry.ram.split("/")[1].trim()}</span>
            </h3>
          </SpotlightCard>
        </section>

        <SpotlightCard className="p-0">
          <div className="p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-zinc-900 pb-4 mb-1">
              <h3 className="font-semibold text-xs tracking-wider text-zinc-350 uppercase flex items-center gap-2">
                <Activity className="h-4 w-4 text-emerald-500" />
                <span>OpenTelemetry Connection Status</span>
              </h3>
            </div>
            
            <div className="flex items-center gap-2 border border-zinc-900 bg-zinc-950/40 px-3 py-1.5 rounded w-fit">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-[10px] font-mono font-medium tracking-wider text-zinc-400">
                OTel Exporter: Active
              </span>
            </div>
            
            <p className="text-xs text-zinc-450 max-w-2xl leading-relaxed mt-1">
              Telemetry spans are exported over HTTP/gRPC formats to the collector endpoint configured at <code className="bg-zinc-900 border border-zinc-850 px-1.5 py-0.5 rounded font-mono text-zinc-300 text-[10px]">http://localhost:4317</code>.
            </p>
          </div>
        </SpotlightCard>
      </main>
    </div>
  );
}
