"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Cpu, ArrowLeft, Plus, Settings2, Sliders } from "lucide-react";

export default function AgentsPage() {
  const [agents, setAgents] = useState([
    { id: "researcher_llama", model: "llama3:8b", role: "Researcher", temp: 0.2, maxTokens: 4096 },
    { id: "writer_llama", model: "llama3:8b", role: "Copywriter", temp: 0.7, maxTokens: 2048 },
    { id: "triager_phi", model: "phi3:medium", role: "Triager", temp: 0.0, maxTokens: 1024 },
  ]);

  return (
    <div className="flex flex-col min-h-screen bg-zinc-950 text-zinc-50">
      <header className="flex items-center justify-between border-b border-zinc-800 bg-zinc-900/50 backdrop-blur px-6 py-4">
        <div className="flex items-center gap-4">
          <Link href="/" className="p-1 bg-zinc-800 hover:bg-zinc-700 rounded transition text-zinc-300">
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div className="flex items-center gap-2">
            <Cpu className="h-6 w-6 text-emerald-500" />
            <span className="font-bold text-lg text-zinc-100">Agent Registry</span>
          </div>
        </div>
        <button className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 px-4 py-2 rounded-lg text-sm font-semibold transition">
          <Plus className="h-4 w-4" /> Register Agent
        </button>
      </header>

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full flex flex-col gap-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {agents.map((agent) => (
            <div key={agent.id} className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 flex flex-col gap-4 hover:border-zinc-700 transition">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-semibold text-zinc-200 text-base">{agent.id}</h4>
                  <span className="text-xs text-zinc-500 font-mono mt-1 block">{agent.model}</span>
                </div>
                <span className="bg-zinc-800 text-zinc-400 text-xs px-2.5 py-1 rounded-full font-medium">
                  {agent.role}
                </span>
              </div>

              <div className="border-t border-zinc-800/80 pt-4 flex flex-col gap-2 text-xs text-zinc-400 font-mono">
                <div className="flex justify-between">
                  <span>Temperature:</span>
                  <span className="text-zinc-300">{agent.temp}</span>
                </div>
                <div className="flex justify-between">
                  <span>Max Tokens:</span>
                  <span className="text-zinc-300">{agent.maxTokens}</span>
                </div>
              </div>

              <div className="flex gap-2 mt-2">
                <button className="flex-1 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition text-zinc-300">
                  <Sliders className="h-3.5 w-3.5" /> Adjust Parameters
                </button>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
