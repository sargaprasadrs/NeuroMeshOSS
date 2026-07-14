"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Layers, ArrowLeft } from "lucide-react";
import { SpotlightCard } from "@/components/SpotlightCard";

export default function WorkflowsPage() {
  const [runs, setRuns] = useState([
    { id: "run_4382", workflow: "Market Analyzer Agent Flow", status: "SUCCESS", duration: "1.4s", timestamp: "2026-07-02 19:15:06" },
    { id: "run_8291", workflow: "Customer Support Triager", status: "RUNNING", duration: "4.2s", timestamp: "2026-07-02 19:17:12" },
    { id: "run_1029", workflow: "Automated Code Review Agent", status: "FAILED", duration: "0.8s", timestamp: "2026-07-02 19:10:45" },
  ]);

  return (
    <div className="flex flex-col min-h-screen bg-black text-zinc-50 font-sans">
      <header className="flex items-center justify-between border-b border-zinc-900 bg-black px-6 py-4 relative z-50">
        <div className="flex items-center gap-4">
          <Link href="/" className="p-1.5 hover:bg-zinc-900 border border-zinc-900 rounded transition text-zinc-400 hover:text-zinc-200 flex items-center justify-center">
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div className="flex items-center gap-2.5">
            <div className="h-5 w-5 rounded bg-emerald-500 flex items-center justify-center">
              <Layers className="h-3 w-3 text-black stroke-[2.5]" />
            </div>
            <span className="font-semibold text-sm tracking-tight text-zinc-100">
              Workflows
            </span>
          </div>
        </div>
      </header>

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full flex flex-col gap-6">
        <SpotlightCard className="p-0">
          <div className="p-6 flex flex-col gap-5">
            <div className="flex items-center justify-between border-b border-zinc-900 pb-4">
              <h3 className="font-semibold text-xs tracking-wider text-zinc-350 uppercase">
                Execution runs
              </h3>
              <span className="text-[10px] text-zinc-550 font-mono">3 executions</span>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-[11px] font-sans">
                <thead>
                  <tr className="border-b border-zinc-900 text-[10px] font-bold text-zinc-500 uppercase tracking-wider">
                    <th className="py-3 px-4 font-semibold">Run ID</th>
                    <th className="py-3 px-4 font-semibold">Workflow</th>
                    <th className="py-3 px-4 font-semibold">Status</th>
                    <th className="py-3 px-4 font-semibold">Duration</th>
                    <th className="py-3 px-4 font-semibold">Started</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-900/60">
                  {runs.map((run) => (
                    <tr key={run.id} className="hover:bg-zinc-900/10 transition duration-150">
                      <td className="py-4 px-4 font-mono text-zinc-400 font-medium">{run.id}</td>
                      <td className="py-4 px-4 text-zinc-200 font-semibold">{run.workflow}</td>
                      <td className="py-4 px-4">
                        <span className={`inline-flex items-center gap-1.5 text-xs font-semibold ${
                          run.status === "SUCCESS" ? "text-emerald-400" :
                          run.status === "RUNNING" ? "text-blue-400" :
                          "text-red-450"
                        }`}>
                          <span className={`h-1.5 w-1.5 rounded-full ${
                            run.status === "SUCCESS" ? "bg-emerald-500" :
                            run.status === "RUNNING" ? "bg-blue-500 animate-pulse" :
                            "bg-red-500"
                          }`} />
                          {run.status.toLowerCase()}
                        </span>
                      </td>
                      <td className="py-4 px-4 text-zinc-400 font-medium font-mono">{run.duration}</td>
                      <td className="py-4 px-4 text-zinc-500 font-medium">{run.timestamp}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </SpotlightCard>
      </main>
    </div>
  );
}
