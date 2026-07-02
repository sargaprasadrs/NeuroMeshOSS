"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Layers, ArrowLeft, ToggleLeft, ToggleRight, DownloadCloud, Sparkles } from "lucide-react";

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
    <div className="flex flex-col min-h-screen bg-zinc-950 text-zinc-50">
      <header className="flex items-center justify-between border-b border-zinc-800 bg-zinc-900/50 backdrop-blur px-6 py-4">
        <div className="flex items-center gap-4">
          <Link href="/" className="p-1 bg-zinc-800 hover:bg-zinc-700 rounded transition text-zinc-300">
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div className="flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-emerald-500" />
            <span className="font-bold text-lg text-zinc-100">Plugin Manager</span>
          </div>
        </div>
        <button className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 px-4 py-2 rounded-lg text-sm font-semibold transition">
          <DownloadCloud className="h-4 w-4" /> Install from Marketplace
        </button>
      </header>

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full flex flex-col gap-6">
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-6 flex flex-col gap-4">
          <h3 className="font-semibold text-lg text-zinc-200">Installed Plugins</h3>
          <div className="flex flex-col gap-3">
            {plugins.map((plugin, index) => (
              <div key={plugin.name} className="flex flex-col md:flex-row md:items-center justify-between bg-zinc-900/60 border border-zinc-800 p-5 rounded-xl gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h4 className="font-semibold text-zinc-200">{plugin.name}</h4>
                    <span className="text-xs bg-zinc-800 text-zinc-500 font-mono px-2 py-0.5 rounded">v{plugin.version}</span>
                  </div>
                  <p className="text-sm text-zinc-400 mt-2 max-w-xl">{plugin.desc}</p>
                </div>
                <div className="flex items-center gap-4">
                  <button onClick={() => togglePlugin(index)} className="focus:outline-none transition">
                    {plugin.active ? (
                      <ToggleRight className="h-9 w-9 text-emerald-500" />
                    ) : (
                      <ToggleLeft className="h-9 w-9 text-zinc-600" />
                    )}
                  </button>
                  <span className={`text-xs font-semibold ${plugin.active ? "text-emerald-500" : "text-zinc-500"}`}>
                    {plugin.active ? "Enabled" : "Disabled"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
