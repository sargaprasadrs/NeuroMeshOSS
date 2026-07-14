"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowLeft, ToggleLeft, ToggleRight, DownloadCloud, Sparkles } from "lucide-react";
import { SpotlightCard } from "@/components/SpotlightCard";

export default function PluginsPage() {
  const [plugins, setPlugins] = useState([
    { name: "github-sync", version: "0.1.0", desc: "Syncs workflow configurations with remote GitHub Git repositories.", active: true },
    { name: "slack-notification", version: "0.1.0", desc: "Posts real-time execution summaries and approvals to Slack channels.", active: true },
    { name: "filesystem-tool", version: "0.1.0", desc: "Enables secure local file operations for executing agent nodes.", active: false },
  ]);

  const togglePlugin = (index: number) => {
    setPlugins((prev) =>
      prev.map((p, i) => (i === index ? { ...p, active: !p.active } : p))
    );
  };

  return (
    <div className="flex flex-col min-h-screen bg-black text-zinc-50 font-sans">
      <header className="flex items-center justify-between border-b border-zinc-900 bg-black px-6 py-4 relative z-50">
        <div className="flex items-center gap-4">
          <Link href="/" className="p-1.5 hover:bg-zinc-900 border border-zinc-900 rounded transition text-zinc-400 hover:text-zinc-200 flex items-center justify-center">
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div className="flex items-center gap-2.5">
            <div className="h-5 w-5 rounded bg-emerald-500 flex items-center justify-center">
              <Sparkles className="h-3 w-3 text-black stroke-[2.5]" />
            </div>
            <span className="font-semibold text-sm tracking-tight text-zinc-100">
              Plugins
            </span>
          </div>
        </div>
        <button className="flex items-center gap-1.5 bg-zinc-100 hover:bg-zinc-200 text-black text-xs font-semibold px-4 py-2 rounded transition-colors duration-150">
          <DownloadCloud className="h-3.5 w-3.5 stroke-[2.5]" /> Install Plugin
        </button>
      </header>

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full flex flex-col gap-6">
        <SpotlightCard className="p-0">
          <div className="p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-zinc-900 pb-4 mb-2">
              <h3 className="font-semibold text-xs tracking-wider text-zinc-350 uppercase">
                Installed Plugins
              </h3>
              <span className="text-[10px] text-zinc-550 font-mono">3 plugins active</span>
            </div>
            
            <div className="flex flex-col gap-3">
              {plugins.map((plugin, index) => (
                <div key={plugin.name} className="flex flex-col md:flex-row md:items-center justify-between border border-zinc-900 bg-zinc-950/40 p-5 rounded-lg gap-4 hover:border-zinc-800 transition duration-150">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h4 className="font-semibold text-sm text-zinc-200">{plugin.name}</h4>
                      <span className="text-[10px] bg-zinc-900 text-zinc-400 font-mono px-2 py-0.5 rounded border border-zinc-850">
                        v{plugin.version}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-450 mt-2.5 max-w-xl leading-relaxed">
                      {plugin.desc}
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-4 md:border-l md:border-zinc-900 md:pl-6">
                    <button onClick={() => togglePlugin(index)} className="focus:outline-none transition active:scale-95 text-zinc-450 hover:text-zinc-200">
                      {plugin.active ? (
                        <ToggleRight className="h-8 w-8 text-emerald-500" />
                      ) : (
                        <ToggleLeft className="h-8 w-8 text-zinc-700" />
                      )}
                    </button>
                    <span className={`text-[10px] font-semibold uppercase tracking-wider w-16 ${plugin.active ? "text-emerald-500" : "text-zinc-500"}`}>
                      {plugin.active ? "Active" : "Disabled"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </SpotlightCard>
      </main>
    </div>
  );
}
