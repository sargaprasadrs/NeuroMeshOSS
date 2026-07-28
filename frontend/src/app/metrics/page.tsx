"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Activity, ArrowLeft, BarChart2, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface HealthStatus {
  status: string;
  database: string;
  queue: string;
}

export default function MetricsPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const { data } = await apiClient.get("/healthz/ready", {
          baseURL: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}`,
        });
        setHealth(data);
      } catch (err: any) {
        setError("Unable to connect to backend");
      } finally {
        setLoading(false);
      }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

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
        {loading ? (
          <div className="flex items-center justify-center py-12 text-zinc-500">
            <Loader2 className="h-5 w-5 animate-spin mr-2" />
            Fetching health status...
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-zinc-900/40 border border-zinc-800 p-4 rounded-xl">
                <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">API Status</p>
                <h3 className={`text-2xl font-bold mt-1 ${health?.status === "ready" ? "text-emerald-400" : "text-red-400"}`}>
                  {health?.status?.toUpperCase() || "UNKNOWN"}
                </h3>
              </div>
              <div className="bg-zinc-900/40 border border-zinc-800 p-4 rounded-xl">
                <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">PostgreSQL</p>
                <h3 className={`text-2xl font-bold mt-1 ${health?.database === "up" ? "text-emerald-400" : "text-red-400"}`}>
                  {health?.database?.toUpperCase() || "DOWN"}
                </h3>
              </div>
              <div className="bg-zinc-900/40 border border-zinc-800 p-4 rounded-xl">
                <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Redis Queue</p>
                <h3 className={`text-2xl font-bold mt-1 ${health?.queue === "up" ? "text-emerald-400" : "text-red-400"}`}>
                  {health?.queue?.toUpperCase() || "DOWN"}
                </h3>
              </div>
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm px-6 py-3 rounded-xl">
                {error}
              </div>
            )}

            <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-6 flex flex-col gap-4">
              <h3 className="font-semibold text-lg text-zinc-200 flex items-center gap-2">
                <Activity className="h-5 w-5 text-emerald-500" /> OpenTelemetry Connection Status
              </h3>
              <div className="flex items-center gap-3">
                <span className={`flex h-2 w-2 rounded-full ${health ? "bg-emerald-500 animate-ping" : "bg-zinc-600"}`}></span>
                <span className="text-sm font-semibold text-zinc-300">
                  OTel Exporter: {health ? "Active" : "Disconnected"}
                </span>
              </div>
              <p className="text-sm text-zinc-400 max-w-2xl leading-relaxed">
                Spans and traces are exported over HTTP/gRPC formats to the collector endpoint configured at{" "}
                <code className="bg-zinc-800 px-1.5 py-0.5 rounded font-mono text-zinc-300">http://localhost:4317</code>.
              </p>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
