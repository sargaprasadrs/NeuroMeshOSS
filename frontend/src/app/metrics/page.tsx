"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Activity, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { Header } from "@/components/header";
import { Card } from "@/components/ui/card";

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
          baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
        });
        setHealth(data);
        setError(null);
      } catch {
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
    <div className="min-h-screen">
      <Header />

      <main className="pt-24 pb-16">
        <div className="container-custom">
          <div className="flex items-center gap-4 mb-8">
            <Link href="/" className="p-2 rounded-lg text-neutral-500 hover:text-white hover:bg-white/5 transition-colors">
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-white">Metrics</h1>
              <p className="text-sm text-neutral-500 mt-1">System health and performance telemetry</p>
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-16 text-neutral-500">
              <Loader2 className="h-5 w-5 animate-spin mr-2" />
              Fetching health status...
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <Card className="p-5">
                  <span className="text-label text-neutral-500 block mb-2">API Status</span>
                  <div className={`text-2xl font-bold ${health?.status === "ready" ? "text-emerald-400" : "text-red-400"}`}>
                    {health?.status?.toUpperCase() || "UNKNOWN"}
                  </div>
                </Card>

                <Card className="p-5">
                  <span className="text-label text-neutral-500 block mb-2">PostgreSQL</span>
                  <div className={`text-2xl font-bold ${health?.database === "up" ? "text-emerald-400" : "text-red-400"}`}>
                    {health?.database?.toUpperCase() || "DOWN"}
                  </div>
                </Card>

                <Card className="p-5">
                  <span className="text-label text-neutral-500 block mb-2">Redis Queue</span>
                  <div className={`text-2xl font-bold ${health?.queue === "up" ? "text-emerald-400" : "text-red-400"}`}>
                    {health?.queue?.toUpperCase() || "DOWN"}
                  </div>
                </Card>
              </div>

              {error && (
                <div className="mb-6 bg-red-500/10 border border-red-500/20 text-red-400 text-sm px-4 py-3 rounded-xl">
                  {error}
                </div>
              )}

              <Card className="p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Activity className="h-4 w-4 text-emerald-500" />
                  <h3 className="text-sm font-semibold text-white">OpenTelemetry</h3>
                </div>
                <div className="flex items-center gap-3 mb-3">
                  <span className={`h-2 w-2 rounded-full ${health ? "bg-emerald-500 animate-pulse" : "bg-neutral-600"}`} />
                  <span className="text-sm text-neutral-300">
                    Exporter: {health ? "Active" : "Disconnected"}
                  </span>
                </div>
                <p className="text-sm text-neutral-500">
                  Spans exported to <code className="bg-neutral-800 px-1.5 py-0.5 rounded text-neutral-400">localhost:4317</code>
                </p>
              </Card>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
