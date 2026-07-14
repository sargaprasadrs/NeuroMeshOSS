"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Cpu, ArrowLeft, Plus, Sliders } from "lucide-react";
import { SpotlightCard } from "@/components/SpotlightCard";

export default function AgentsPage() {
  const [agents, setAgents] = useState([
    { id: "researcher_llama", model: "llama3:8b", role: "Researcher", temp: 0.2, maxTokens: 4096 },
    { id: "writer_llama", model: "llama3:8b", role: "Copywriter", temp: 0.7, maxTokens: 2048 },
    { id: "triager_phi", model: "phi3:medium", role: "Triager", temp: 0.0, maxTokens: 1024 },
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
              <Cpu className="h-3 w-3 text-black stroke-[2.5]" />
            </div>
            <span className="font-semibold text-sm tracking-tight text-zinc-100">
              Agents
            </span>
          </div>
        </div>
        <button className="flex items-center gap-1.5 bg-zinc-100 hover:bg-zinc-200 text-black text-xs font-semibold px-4 py-2 rounded transition-colors duration-150">
          <Plus className="h-3.5 w-3.5 stroke-[2.5]" /> Register Agent
        </button>
      </header>

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full flex flex-col gap-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {agents.map((agent) => (
            <SpotlightCard key={agent.id} className="flex flex-col p-5">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="font-semibold text-zinc-200 text-sm tracking-tight">{agent.id}</h4>
                  <span className="text-[10px] text-zinc-500 font-mono mt-0.5 block">{agent.model}</span>
                </div>
                <span className="bg-zinc-900 text-zinc-400 text-[10px] font-semibold px-2 py-0.5 rounded border border-zinc-800">
                  {agent.role}
                </span>
              </div>

              <div className="border-t border-zinc-900 pt-4 flex flex-col gap-2.5 text-xs text-zinc-400 font-sans">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Temperature</span>
                  <span className="text-zinc-350 font-mono font-medium">{agent.temp}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Max Tokens</span>
                  <span className="text-zinc-350 font-mono font-medium">{agent.maxTokens}</span>
                </div>
              </div>

              <div className="flex gap-2 mt-5">
                <button className="flex-1 py-2 bg-zinc-950 hover:bg-zinc-900 border border-zinc-900 rounded text-xs font-semibold flex items-center justify-center gap-1.5 transition text-zinc-300 hover:text-zinc-100">
                  <Sliders className="h-3.5 w-3.5" /> Adjust Parameters
                </button>
              </div>
            </SpotlightCard>
          ))}
        </div>
      </main>
    </div>
  );
}
