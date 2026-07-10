"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Layers, ArrowLeft, Play, Clock, CheckCircle2, XCircle } from "lucide-react";

export default function WorkflowsPage() {
  const [runs, setRuns] = useState([
    { id: "run_4382", workflow: "Market Analyzer Agent Flow", status: "SUCCESS", duration: "1.4s", timestamp: "2026-07-02 19:15:06" },
    { id: "run_8291", workflow: "Customer Support Triager", status: "RUNNING", duration: "4.2s", timestamp: "2026-07-02 19:17:12" },
    { id: "run_1029", workflow: "Automated Code Review Agent", status: "FAILED", duration: "0.8s", timestamp: "2026-07-02 19:10:45" },
  ]);

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

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full flex flex-col gap-6">
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-6 flex flex-col gap-4">
          <h3 className="font-semibold text-lg text-zinc-200">Execution Runs</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-zinc-850 text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Run ID</th>
                  <th className="py-3 px-4">Workflow Name</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Duration</th>
                  <th className="py-3 px-4">Triggered Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900 text-sm">
                {runs.map((run) => (
                  <tr key={run.id} className="hover:bg-zinc-900/30 transition">
                    <td className="py-3 px-4 font-mono text-emerald-400">{run.id}</td>
                    <td className="py-3 px-4 font-medium text-zinc-300">{run.workflow}</td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-semibold ${
                        run.status === "SUCCESS" ? "bg-emerald-500/10 text-emerald-500" :
                        run.status === "RUNNING" ? "bg-blue-500/10 text-blue-400" :
                        "bg-red-500/10 text-red-500"
                      }`}>
                        {run.status === "SUCCESS" && <CheckCircle2 className="h-3 w-3" />}
                        {run.status === "RUNNING" && <Clock className="h-3 w-3 animate-spin" />}
                        {run.status === "FAILED" && <XCircle className="h-3 w-3" />}
                        {run.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-zinc-400">{run.duration}</td>
                    <td className="py-3 px-4 text-zinc-500">{run.timestamp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
